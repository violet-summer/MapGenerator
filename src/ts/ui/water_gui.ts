import * as log from 'loglevel';
import CanvasWrapper from './canvas_wrapper';
import DomainController from './domain_controller';
import Util from '../util';
import FieldIntegrator from '../impl/integrator';
import { StreamlineParams } from '../impl/streamlines';
import { WaterParams } from '../impl/water_generator';
import WaterGenerator from '../impl/water_generator';
import Vector from '../vector';
import PolygonFinder from '../impl/polygon_finder';
import PolygonUtil from '../impl/polygon_util';
import RoadGUI from './road_gui';
import { NoiseParams } from '../impl/tensor_field';
import TensorField from '../impl/tensor_field';

/**
 * Handles generation of river and coastline
 */
export default class WaterGUI extends RoadGUI {
    protected streamlines: WaterGenerator; // 用于生成河流和海岸线的流线生成器

    constructor(
        private tensorField: TensorField, // 张量场，用于生成流线
        protected params: WaterParams, // 水体生成的参数
        integrator: FieldIntegrator, // 流线积分器
        guiFolder: dat.GUI, // dat.GUI 文件夹
        closeTensorFolder: () => void, // 关闭张量场文件夹的回调
        folderName: string, // 文件夹名称
        redraw: () => void // 重绘回调
    ) {
        super(params, integrator, guiFolder, closeTensorFolder, folderName, redraw);
        this.streamlines = new WaterGenerator(
            this.integrator,
            this.domainController.origin,
            this.domainController.worldDimensions,
            Object.assign({}, this.params),
            this.tensorField
        );
    }

    initFolder(): WaterGUI {
        // 初始化 dat.GUI 文件夹
        const folder = this.guiFolder.addFolder(this.folderName);
        folder.add({ Generate: () => this.generateRoads() }, 'Generate');

        const coastParamsFolder = folder.addFolder('CoastParams'); // 海岸线参数
        coastParamsFolder.add(this.params.coastNoise, 'noiseEnabled');
        coastParamsFolder.add(this.params.coastNoise, 'noiseSize');
        coastParamsFolder.add(this.params.coastNoise, 'noiseAngle');
        const riverParamsFolder = folder.addFolder('RiverParams'); // 河流参数
        riverParamsFolder.add(this.params.riverNoise, 'noiseEnabled');
        riverParamsFolder.add(this.params.riverNoise, 'noiseSize');
        riverParamsFolder.add(this.params.riverNoise, 'noiseAngle');

        folder.add(this.params, 'simplifyTolerance'); // 简化容差
        const devParamsFolder = folder.addFolder('Dev'); // 开发参数
        this.addDevParamsToFolder(this.params, devParamsFolder);
        return this;
    }

    generateRoads(): Promise<void> {
        // 生成河流和海岸线
        this.preGenerateCallback();

        this.domainController.zoom = this.domainController.zoom / Util.DRAW_INFLATE_AMOUNT;
        this.streamlines = new WaterGenerator(
            this.integrator,
            this.domainController.origin,
            this.domainController.worldDimensions,
            Object.assign({}, this.params),
            this.tensorField
        );
        this.domainController.zoom = this.domainController.zoom * Util.DRAW_INFLATE_AMOUNT;

        this.streamlines.createCoast(); // 创建海岸线
        this.streamlines.createRiver(); // 创建河流

        this.closeTensorFolder();
        this.redraw();
        this.postGenerateCallback();
        return new Promise<void>((resolve) => resolve());
    }

    /**
     * Secondary road runs along other side of river
     */
    get streamlinesWithSecondaryRoad(): Vector[][] {
        // 包含次级道路的流线
        const withSecondary = this.streamlines.allStreamlinesSimple.slice();
        withSecondary.push(this.streamlines.riverSecondaryRoad);
        return withSecondary;
    }

    get river(): Vector[] {
        // 获取河流的屏幕坐标
        return this.streamlines.riverPolygon.map((v) =>
            this.domainController.worldToScreen(v.clone())
        );
    }

    get secondaryRiver(): Vector[] {
        // 获取次级河流的屏幕坐标
        return this.streamlines.riverSecondaryRoad.map((v) =>
            this.domainController.worldToScreen(v.clone())
        );
    }

    get coastline(): Vector[] {
        // 获取海岸线的屏幕坐标
        return this.streamlines.coastline.map((v) =>
            this.domainController.worldToScreen(v.clone())
        );
    }

    get seaPolygon(): Vector[] {
        // 获取海洋多边形的屏幕坐标
        return this.streamlines.seaPolygon.map((v) =>
            this.domainController.worldToScreen(v.clone())
        );
    }

    protected addDevParamsToFolder(params: StreamlineParams, folder: dat.GUI): void {
        // 添加开发参数到 dat.GUI 文件夹
        folder.add(params, 'dsep');
        folder.add(params, 'dtest');
        folder.add(params, 'pathIterations');
        folder.add(params, 'seedTries');
        folder.add(params, 'dstep');
        folder.add(params, 'dlookahead');
        folder.add(params, 'dcirclejoin');
        folder.add(params, 'joinangle');
    }
    
}
