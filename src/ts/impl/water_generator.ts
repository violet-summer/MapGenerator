import * as log from 'loglevel';
import Vector from '../vector';
import FieldIntegrator from './integrator';
import StreamlineGenerator from './streamlines';
import { StreamlineParams } from './streamlines';
import TensorField from './tensor_field';
import PolygonUtil from './polygon_util';

export interface WaterParams extends StreamlineParams {
    coastNoise: NoiseStreamlineParams; // 海岸线噪声参数
    riverNoise: NoiseStreamlineParams; // 河流噪声参数
    riverBankSize: number; // 河岸宽度
    riverSize: number; // 河流宽度
}

export interface NoiseStreamlineParams {
    noiseEnabled: boolean; // 是否启用噪声
    noiseSize: number; // 噪声大小
    noiseAngle: number; // 噪声角度
}

/**
 * WaterGenerator 类
 * 用于生成海岸线和河流的流线，并支持可控的噪声。
 */
export default class WaterGenerator extends StreamlineGenerator {
    private readonly TRIES = 100; // 最大尝试次数
    private coastlineMajor = true; // 是否为主要海岸线
    private _coastline: Vector[] = []; // 噪声化的海岸线
    private _seaPolygon: Vector[] = []; // 海洋多边形
    private _riverPolygon: Vector[] = []; // 河流多边形
    private _riverSecondaryRoad: Vector[] = []; // 河流次级道路

    constructor(
        integrator: FieldIntegrator, // 流线积分器
        origin: Vector, // 世界坐标原点
        worldDimensions: Vector, // 世界坐标尺寸
        protected params: WaterParams, // 水体生成参数
        private tensorField: TensorField // 张量场
    ) {
        super(integrator, origin, worldDimensions, params);
    }

    get coastline(): Vector[] {
        return this._coastline;
    }

    get seaPolygon(): Vector[] {
        return this._seaPolygon;
    }

    get riverPolygon(): Vector[] {
        return this._riverPolygon;
    }

    get riverSecondaryRoad(): Vector[] {
        return this._riverSecondaryRoad;
    }

    /**
     * 创建海岸线
     */
    createCoast(): void {
        let coastStreamline;
        let seed;
        let major;

        if (this.params.coastNoise.noiseEnabled) {
            this.tensorField.enableGlobalNoise(
                this.params.coastNoise.noiseAngle,
                this.params.coastNoise.noiseSize
            );
        }
        for (let i = 0; i < this.TRIES; i++) {
            major = Math.random() < 0.5;
            seed = this.getSeed(major);
            coastStreamline = this.extendStreamline(this.integrateStreamline(seed, major));

            if (this.reachesEdges(coastStreamline)) {
                break;
            }
        }
        this.tensorField.disableGlobalNoise();

        this._coastline = coastStreamline;
        this.coastlineMajor = major;

        const road = this.simplifyStreamline(coastStreamline);
        this._seaPolygon = this.getSeaPolygon(road);
        this.allStreamlinesSimple.push(road);
        this.tensorField.sea = this._seaPolygon;

        // 创建中间采样点
        const complex = this.complexifyStreamline(road);
        this.grid(major).addPolyline(complex);
        this.streamlines(major).push(complex);
        this.allStreamlines.push(complex);
    }

    /**
     * 创建河流
     */
    createRiver(): void {
        let riverStreamline;
        let seed;

        // 忽略海洋以便进行边界检查
        const oldSea = this.tensorField.sea;
        this.tensorField.sea = [];
        if (this.params.riverNoise.noiseEnabled) {
            this.tensorField.enableGlobalNoise(
                this.params.riverNoise.noiseAngle,
                this.params.riverNoise.noiseSize
            );
        }
        for (let i = 0; i < this.TRIES; i++) {
            seed = this.getSeed(!this.coastlineMajor);
            riverStreamline = this.extendStreamline(this.integrateStreamline(seed, !this.coastlineMajor));

            if (this.reachesEdges(riverStreamline)) {
                break;
            } else if (i === this.TRIES - 1) {
                log.error('Failed to find river reaching edge');
            }
        }
        this.tensorField.sea = oldSea;
        this.tensorField.disableGlobalNoise();

        // 创建河流道路
        const expandedNoisy = this.complexifyStreamline(
            PolygonUtil.resizeGeometry(riverStreamline, this.params.riverSize, false)
        );
        this._riverPolygon = PolygonUtil.resizeGeometry(
            riverStreamline,
            this.params.riverSize - this.params.riverBankSize,
            false
        );

        // 创建河流次级道路
        const riverSplitPoly = this.getSeaPolygon(riverStreamline);
        const road1 = expandedNoisy.filter(
            (v) =>
                !PolygonUtil.insidePolygon(v, this._seaPolygon) &&
                !this.vectorOffScreen(v) &&
                PolygonUtil.insidePolygon(v, riverSplitPoly)
        );
        const road1Simple = this.simplifyStreamline(road1);
        const road2 = expandedNoisy.filter(
            (v) =>
                !PolygonUtil.insidePolygon(v, this._seaPolygon) &&
                !this.vectorOffScreen(v) &&
                !PolygonUtil.insidePolygon(v, riverSplitPoly)
        );
        const road2Simple = this.simplifyStreamline(road2);

        if (road1.length === 0 || road2.length === 0) return;

        if (
            road1[0].distanceToSquared(road2[0]) <
            road1[0].distanceToSquared(road2[road2.length - 1])
        ) {
            road2Simple.reverse();
        }

        this.tensorField.river = road1Simple.concat(road2Simple);

        // 保存次级道路
        this.allStreamlinesSimple.push(road1Simple);
        this._riverSecondaryRoad = road2Simple;

        this.grid(!this.coastlineMajor).addPolyline(road1);
        this.grid(!this.coastlineMajor).addPolyline(road2);
        this.streamlines(!this.coastlineMajor).push(road1);
        this.streamlines(!this.coastlineMajor).push(road2);
        this.allStreamlines.push(road1);
        this.allStreamlines.push(road2);
    }

    /**
     * 假设简化
     * 用于添加河流道路
     */
    private manuallyAddStreamline(s: Vector[], major: boolean): void {
        this.allStreamlinesSimple.push(s);
        // 创建中间采样点
        const complex = this.complexifyStreamline(s);
        this.grid(major).addPolyline(complex);
        this.streamlines(major).push(complex);
        this.allStreamlines.push(complex);
    }

    /**
     * 可能会反转输入数组
     */
    private getSeaPolygon(polyline: Vector[]): Vector[] {
        return PolygonUtil.lineRectanglePolygonIntersection(this.origin, this.worldDimensions, polyline);
    }

    /**
     * 在流线上插入样本，直到样本间距为 dstep
     */
    private complexifyStreamline(s: Vector[]): Vector[] {
        const out: Vector[] = [];
        for (let i = 0; i < s.length - 1; i++) {
            out.push(...this.complexifyStreamlineRecursive(s[i], s[i + 1]));
        }
        return out;
    }

    private complexifyStreamlineRecursive(v1: Vector, v2: Vector): Vector[] {
        if (v1.distanceToSquared(v2) <= this.paramsSq.dstep) {
            return [v1, v2];
        }
        const d = v2.clone().sub(v1);
        const halfway = v1.clone().add(d.multiplyScalar(0.5));

        const complex = this.complexifyStreamlineRecursive(v1, halfway);
        complex.push(...this.complexifyStreamlineRecursive(halfway, v2));
        return complex;
    }

    /**
     * 扩展流线
     * 变异流线
     */
    private extendStreamline(streamline: Vector[]): Vector[] {
        streamline.unshift(
            streamline[0]
                .clone()
                .add(streamline[0].clone().sub(streamline[1]).setLength(this.params.dstep * 5))
        );
        streamline.push(
            streamline[streamline.length - 1]
                .clone()
                .add(
                    streamline[streamline.length - 1]
                        .clone()
                        .sub(streamline[streamline.length - 2])
                        .setLength(this.params.dstep * 5)
                )
        );
        return streamline;
    }

    /**
     * 检查流线是否到达边界
     */
    private reachesEdges(streamline: Vector[]): boolean {
        return (
            this.vectorOffScreen(streamline[0]) &&
            this.vectorOffScreen(streamline[streamline.length - 1])
        );
    }

    /**
     * 检查向量是否在屏幕外
     */
    private vectorOffScreen(v: Vector): boolean {
        const toOrigin = v.clone().sub(this.origin);
        return (
            toOrigin.x <= 0 ||
            toOrigin.y <= 0 ||
            toOrigin.x >= this.worldDimensions.x ||
            toOrigin.y >= this.worldDimensions.y
        );
    }
}
