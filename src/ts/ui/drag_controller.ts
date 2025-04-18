import * as log from 'loglevel';
import interact from 'interactjs';
import Util from '../util';
import Vector from '../Vector';
import DomainController from './domain_controller';

interface Draggable {
    getCentre: (() => Vector); // 获取中心点的回调函数
    startListener: (() => void); // 拖动开始时的回调函数
    moveListener: ((v: Vector) => void); // 拖动时的回调函数
}

/**
 * DragController 类
 * 管理画布的拖拽交互，支持多中心点的拖拽选择。
 * 最近的中心点会被选中进行拖拽。
 */
export default class DragController {
    // 指针需要靠近拖动句柄的最小距离
    private readonly MIN_DRAG_DISTANCE = 50;

    private draggables: Draggable[] = []; // 可拖动对象的列表
    private currentlyDragging: Draggable = null; // 当前正在拖动的对象
    private _isDragging = false; // 是否正在拖动
    private disabled: boolean = false; // 是否禁用拖动
    private domainController = DomainController.getInstance(); // 域控制器实例

    constructor(private gui: dat.GUI) {
        // 初始化 interact.js 的拖拽功能
        interact(`#${Util.CANVAS_ID}`).draggable({
            onstart: this.dragStart.bind(this), // 拖动开始事件
            onmove: this.dragMove.bind(this), // 拖动移动事件
            onend: this.dragEnd.bind(this), // 拖动结束事件
            cursorChecker: this.getCursor.bind(this), // 自定义光标样式
        });
    }

    setDragDisabled(disable: boolean): void {
        // 启用或禁用拖动功能
        this.disabled = disable;
    }

    /**
     * 自定义光标样式
     */
    getCursor(action: any, interactable: any, element: any, interacting: boolean): string {
        if (interacting) return 'grabbing'; // 拖动时显示抓取手势
        return 'grab'; // 默认显示抓取手势
    }

    dragStart(event: any): void {
        // 拖动开始事件处理
        this._isDragging = true;

        // 将屏幕坐标转换为世界坐标
        const origin = this.domainController.screenToWorld(new Vector(event.x0, event.y0));

        let closestDistance = Infinity;
        this.draggables.forEach(draggable => {
            const d = draggable.getCentre().distanceTo(origin); // 计算与中心点的距离
            if (d < closestDistance) {
                closestDistance = d;
                this.currentlyDragging = draggable; // 选择最近的中心点
            }
        });

        // 根据缩放比例调整拖动距离
        const scaledDragDistance = this.MIN_DRAG_DISTANCE / this.domainController.zoom;

        if (closestDistance > scaledDragDistance) {
            this.currentlyDragging = null; // 如果距离过远，不选择任何对象
        } else {
            this.currentlyDragging.startListener(); // 调用拖动开始回调
        }
    }

    dragMove(event: any): void {
        // 拖动移动事件处理
        const delta = new Vector(event.delta.x, event.delta.y); // 获取拖动的增量
        this.domainController.zoomToWorld(delta); // 将增量转换为世界坐标

        if (!this.disabled && this.currentlyDragging !== null) {
            // 拖动对象
            this.currentlyDragging.moveListener(delta);
        } else {
            // 拖动地图
            this.domainController.pan(delta);
        }
    }

    dragEnd(): void {
        // 拖动结束事件处理
        this._isDragging = false;
        this.domainController.pan(Vector.zeroVector()); // 触发画布更新
        this.currentlyDragging = null;
        Util.updateGui(this.gui); // 更新 dat.GUI 的显示
    }

    get isDragging(): boolean {
        // 返回是否正在拖动
        return this._isDragging;
    }

    /**
     * 注册一个可拖动对象
     * @param {(() => Vector)} getCentre 获取中心点的回调函数
     * @param {((v: Vector) => void)} onMove 拖动时的回调函数
     * @param {(() => void)} onStart 拖动开始时的回调函数
     * @returns {(() => void)} 返回一个函数，用于取消注册
     */
    register(
        getCentre: (() => Vector),
        onMove: ((v: Vector) => void),
        onStart: (() => void),
    ): (() => void) {
        const draggable: Draggable = {
            getCentre: getCentre,
            moveListener: onMove,
            startListener: onStart,
        };

        this.draggables.push(draggable); // 添加到可拖动对象列表
        return ((): void => {
            const index = this.draggables.indexOf(draggable);
            if (index >= 0) {
                this.draggables.splice(index, 1); // 从列表中移除
            }
        }).bind(this);
    }
}
