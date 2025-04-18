import * as log from 'loglevel';
import Vector from '../vector';
import Util from '../util';

/**
 * Singleton
 * Controls panning and zooming
 * 管理画布的平移和缩放
 */
export default class DomainController {
    private static instance: DomainController;

    private readonly ZOOM_SPEED = 0.96; // 缩放速度
    private readonly SCROLL_DELAY = 100; // 滚动延迟（毫秒）

    // Location of screen origin in world space
    private _origin: Vector = Vector.zeroVector(); // 屏幕原点在世界坐标中的位置
    
    // Screen-space width and height
    private _screenDimensions = Vector.zeroVector(); // 屏幕的宽度和高度

    // Ratio of screen pixels to world pixels
    private _zoom: number = 1; // 屏幕像素与世界像素的比例
    private zoomCallback: () => any = () => {}; // 缩放回调函数
    private lastScrolltime = -this.SCROLL_DELAY; // 上次滚动的时间戳
    private refreshedAfterScroll = false; // 滚动后是否已刷新

    private _cameraDirection = Vector.zeroVector(); // 相机方向
    private _orthographic = false; // 是否为正交投影

    // Set after pan or zoom
    public moved = false; // 平移或缩放后设置为 true

    private constructor() {
        this.setScreenDimensions(); // 初始化屏幕尺寸

        // 监听窗口大小变化事件
        window.addEventListener('resize', (): void => this.setScreenDimensions());

        // 监听鼠标滚轮事件，用于缩放
        window.addEventListener('wheel', (e: any): void => {
            if (e.target.id === Util.CANVAS_ID) {
                this.lastScrolltime = Date.now();
                this.refreshedAfterScroll = false;
                const delta: number = e.deltaY;
                if (delta > 0) {
                    this.zoom = this._zoom * this.ZOOM_SPEED; // 缩小
                } else {
                    this.zoom = this._zoom / this.ZOOM_SPEED; // 放大
                }
            }
        });
    }

    /**
     * 用于在某些样式下停止滚动时绘制建筑物，以保持帧率
     */
    get isScrolling(): boolean {
        return Date.now() - this.lastScrolltime < this.SCROLL_DELAY;
    }

    private setScreenDimensions(): void {
        // 设置屏幕尺寸
        this.moved = true;
        this._screenDimensions.setX(window.innerWidth);
        this._screenDimensions.setY(window.innerHeight);
    }

    public static getInstance(): DomainController {
        // 获取 DomainController 的单例实例
        if (!DomainController.instance) {
            DomainController.instance = new DomainController();
        }
        return DomainController.instance;
    }

    /**
     * 平移画布
     * @param {Vector} delta 平移的世界坐标增量
     */
    pan(delta: Vector) {
        this.moved = true;
        this._origin.sub(delta);
    }

    /**
     * 获取屏幕原点在世界坐标中的位置
     */
    get origin(): Vector {
        return this._origin.clone();
    }

    get zoom(): number {
        return this._zoom;
    }

    get screenDimensions(): Vector {
        return this._screenDimensions.clone();
    }

    /**
     * 获取屏幕上可见的世界坐标宽度和高度
     */
    get worldDimensions(): Vector {
        return this.screenDimensions.divideScalar(this._zoom);
    }

    set screenDimensions(v: Vector) {
        this.moved = true;
        this._screenDimensions.copy(v);
    }

    set zoom(z: number) {
        // 设置缩放比例
        if (z >= 0.3 && z <= 20) {
            this.moved = true;
            const oldWorldSpaceMidpoint = this.origin.add(this.worldDimensions.divideScalar(2));
            this._zoom = z;
            const newWorldSpaceMidpoint = this.origin.add(this.worldDimensions.divideScalar(2));
            this.pan(newWorldSpaceMidpoint.sub(oldWorldSpaceMidpoint));
            this.zoomCallback();
        }
    }

    onScreen(v: Vector): boolean {
        // 判断一个点是否在屏幕范围内
        const screenSpace = this.worldToScreen(v.clone());
        return screenSpace.x >= 0 && screenSpace.y >= 0
            && screenSpace.x <= this.screenDimensions.x && screenSpace.y <= this.screenDimensions.y;
    }

    set orthographic(v: boolean) {
        this._orthographic = v;
        this.moved = true;
    }

    get orthographic(): boolean {
        return this._orthographic;
    }

    set cameraDirection(v: Vector) {
        this._cameraDirection = v;
        this.moved = true; // 更新屏幕
    }

    get cameraDirection(): Vector {
        return this._cameraDirection.clone();
    }

    getCameraPosition(): Vector {
        // 获取相机位置
        const centre = new Vector(this._screenDimensions.x / 2, this._screenDimensions.y / 2);
        if (this._orthographic) {
            return centre.add(centre.clone().multiply(this._cameraDirection).multiplyScalar(100));
        }
        return centre.add(centre.clone().multiply(this._cameraDirection));
    }

    setZoomUpdate(callback: () => any): void {
        // 设置缩放更新回调
        this.zoomCallback = callback;
    }

    /**
     * 将屏幕坐标转换为世界坐标
     * @param {Vector} v 屏幕坐标
     */
    screenToWorld(v: Vector): Vector {
        return this.zoomToWorld(v).add(this._origin);
    }

    /**
     * 将世界坐标转换为屏幕坐标
     * @param {Vector} v 世界坐标
     */
    worldToScreen(v: Vector): Vector {
        return this.zoomToScreen(v.sub(this._origin));
    }

    /**
     * 将屏幕增量转换为世界增量
     * @param {Vector} v 屏幕增量
     */
    zoomToWorld(v: Vector): Vector {
        return v.divideScalar(this._zoom);
    }

    /**
     * 将世界增量转换为屏幕增量
     * @param {Vector} v 世界增量
     */
    zoomToScreen(v: Vector): Vector {
        return v.multiplyScalar(this._zoom);
    }
}
