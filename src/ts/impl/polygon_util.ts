import * as log from 'loglevel';
import * as PolyK from 'polyk';
import Vector from '../vector';
import * as jsts from 'jsts';

export default class PolygonUtil {
    private static geometryFactory = new jsts.geom.GeometryFactory(); // JSTS 几何工厂，用于创建几何对象

    /**
     * 切割矩形，返回最小的多边形
     * @param origin 矩形的起点
     * @param worldDimensions 矩形的宽高
     * @param p1 切割线的起点
     * @param p2 切割线的终点
     */
    public static sliceRectangle(origin: Vector, worldDimensions: Vector, p1: Vector, p2: Vector): Vector[] {
        const rectangle = [
            origin.x, origin.y,
            origin.x + worldDimensions.x, origin.y,
            origin.x + worldDimensions.x, origin.y + worldDimensions.y,
            origin.x, origin.y + worldDimensions.y,
        ];
        const sliced = PolyK.Slice(rectangle, p1.x, p1.y, p2.x, p2.y).map(p => PolygonUtil.polygonArrayToPolygon(p));
        const minArea = PolygonUtil.calcPolygonArea(sliced[0]);

        if (sliced.length > 1 && PolygonUtil.calcPolygonArea(sliced[1]) < minArea) {
            return sliced[1];
        }

        return sliced[0];
    }

    /**
     * 用于创建海洋多边形
     * @param origin 矩形的起点
     * @param worldDimensions 矩形的宽高
     * @param line 切割线
     */
    public static lineRectanglePolygonIntersection(origin: Vector, worldDimensions: Vector, line: Vector[]): Vector[] {
        const jstsLine = PolygonUtil.lineToJts(line); // 将线转换为 JSTS 几何对象
        const bounds = [
            origin,
            new Vector(origin.x + worldDimensions.x, origin.y),
            new Vector(origin.x + worldDimensions.x, origin.y + worldDimensions.y),
            new Vector(origin.x, origin.y + worldDimensions.y),
        ];
        const boundingPoly = PolygonUtil.polygonToJts(bounds); // 创建矩形的 JSTS 多边形
        const union = boundingPoly.getExteriorRing().union(jstsLine); // 合并边界和线
        const polygonizer = new (jsts.operation as any).polygonize.Polygonizer(); // 创建多边形化器
        polygonizer.add(union);
        const polygons = polygonizer.getPolygons();

        let smallestArea = Infinity;
        let smallestPoly;
        for (let i = polygons.iterator(); i.hasNext();) {
            const polygon = i.next();
            const area = polygon.getArea();
            if (area < smallestArea) {
                smallestArea = area;
                smallestPoly = polygon;
            }
        }

        if (!smallestPoly) return [];
        return smallestPoly.getCoordinates().map((c: any) => new Vector(c.x, c.y));
    }

    /**
     * 计算多边形的面积
     * @param polygon 多边形顶点数组
     */
    public static calcPolygonArea(polygon: Vector[]): number {
        let total = 0;

        for (let i = 0; i < polygon.length; i++) {
            const addX = polygon[i].x;
            const addY = polygon[i == polygon.length - 1 ? 0 : i + 1].y;
            const subX = polygon[i == polygon.length - 1 ? 0 : i + 1].x;
            const subY = polygon[i].y;

            total += (addX * addY * 0.5);
            total -= (subX * subY * 0.5);
        }

        return Math.abs(total);
    }

    /**
     * 递归地将多边形按最长边分割，直到满足最小面积条件
     * @param p 多边形顶点数组
     * @param minArea 最小面积
     */
    public static subdividePolygon(p: Vector[], minArea: number): Vector[][] {
        const area = PolygonUtil.calcPolygonArea(p);
        if (area < 0.5 * minArea) {
            return [];
        }
        const divided: Vector[][] = []; // 分割后的多边形数组

        let longestSideLength = 0;
        let longestSide = [p[0], p[1]];

        let perimeter = 0;

        for (let i = 0; i < p.length; i++) {
            const sideLength = p[i].clone().sub(p[(i+1) % p.length]).length();
            perimeter += sideLength;
            if (sideLength > longestSideLength) {
                longestSideLength = sideLength;
                longestSide = [p[i], p[(i+1) % p.length]];
            }
        }

        // 形状指数
        if (area / (perimeter * perimeter) < 0.04) {
            return [];
        }

        if (area < 2 * minArea) {
            return [p];
        }

        // 偏移量在 0.4 到 0.6 之间
        const deviation = (Math.random() * 0.2) + 0.4;

        const averagePoint = longestSide[0].clone().add(longestSide[1]).multiplyScalar(deviation);
        const differenceVector = longestSide[0].clone().sub(longestSide[1]);
        const perpVector = (new Vector(differenceVector.y, -1 * differenceVector.x))
            .normalize()
            .multiplyScalar(100);

        const bisect = [averagePoint.clone().add(perpVector), averagePoint.clone().sub(perpVector)];

        // 分割多边形
        try {
            const sliced = PolyK.Slice(PolygonUtil.polygonToPolygonArray(p), bisect[0].x, bisect[0].y, bisect[1].x, bisect[1].y);
            for (const s of sliced) {
                divided.push(...PolygonUtil.subdividePolygon(PolygonUtil.polygonArrayToPolygon(s), minArea));
            }

            return divided;
        } catch (error) {
            log.error(error);
            return [];
        }
    }

    /**
     * 缩放多边形
     * @param geometry 多边形顶点数组
     * @param spacing 缩放距离
     * @param isPolygon 是否为多边形
     */
    public static resizeGeometry(geometry: Vector[], spacing: number, isPolygon=true): Vector[] {
        try {
            const jstsGeometry = isPolygon? PolygonUtil.polygonToJts(geometry) : PolygonUtil.lineToJts(geometry);
            const resized = jstsGeometry.buffer(spacing, undefined, (jsts as any).operation.buffer.BufferParameters.CAP_FLAT);
            if (!resized.isSimple()) {
                return [];
            }
            return resized.getCoordinates().map(c => new Vector(c.x, c.y));
        } catch (error) {
            log.error(error);
            return [];
        }
    }

    /**
     * 计算多边形的平均点
     * @param polygon 多边形顶点数组
     */
    public static averagePoint(polygon: Vector[]): Vector {
        if (polygon.length === 0) return Vector.zeroVector();
        const sum = Vector.zeroVector();
        for (const v of polygon) {
            sum.add(v);
        }
        return sum.divideScalar(polygon.length);
    }

    /**
     * 判断点是否在多边形内
     * @param point 点
     * @param polygon 多边形顶点数组
     */
    public static insidePolygon(point: Vector, polygon: Vector[]): boolean {
        // ray-casting algorithm based on
        // http://www.ecse.rpi.edu/Homepages/wrf/Research/Short_Notes/pnpoly.html

        if (polygon.length === 0) {
            return false;
        }

        let inside = false;
        for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
            const xi = polygon[i].x, yi = polygon[i].y;
            const xj = polygon[j].x, yj = polygon[j].y;

            const intersect = ((yi > point.y) != (yj > point.y))
                && (point.x < (xj - xi) * (point.y - yi) / (yj - yi) + xi);
            if (intersect) inside = !inside;
        }

        return inside;
    }

    /**
     * 判断点是否在矩形内
     * @param point 点
     * @param origin 矩形的起点
     * @param dimensions 矩形的宽高
     */
    public static pointInRectangle(point: Vector, origin: Vector, dimensions: Vector): boolean {
        return point.x >= origin.x && point.y >= origin.y && point.x <= dimensions.x && point.y <= dimensions.y;
    }

    /**
     * 将线转换为 JSTS 几何对象
     * @param line 线的顶点数组
     */
    private static lineToJts(line: Vector[]): jsts.geom.LineString {
        const coords = line.map(v => new jsts.geom.Coordinate(v.x, v.y));
        return PolygonUtil.geometryFactory.createLineString(coords);
    }

    /**
     * 将多边形转换为 JSTS 几何对象
     * @param polygon 多边形顶点数组
     */
    private static polygonToJts(polygon: Vector[]): jsts.geom.Polygon {
        const geoInput = polygon.map(v => new jsts.geom.Coordinate(v.x, v.y));
        geoInput.push(geoInput[0]);  // Create loop
        return PolygonUtil.geometryFactory.createPolygon(PolygonUtil.geometryFactory.createLinearRing(geoInput), []);
    }

    /**
     * 将多边形转换为数组
     * @param p 多边形顶点数组
     */
    private static polygonToPolygonArray(p: Vector[]): number[] {
        const outP: number[] = [];
        for (const v of p) {
            outP.push(v.x);
            outP.push(v.y);
        }
        return outP;
    }

    /**
     * 将数组转换为多边形
     * @param p 多边形顶点数组
     */
    private static polygonArrayToPolygon(p: number[]): Vector[] {
        const outP = [];
        for (let i = 0; i < p.length / 2; i++) {
            outP.push(new Vector(p[2*i], p[2*i + 1]));
        }
        return outP;
    }
}
