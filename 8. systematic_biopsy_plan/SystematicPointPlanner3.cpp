#include "SystematicPointPlanner3.h"

#include <QDebug>
#include <vtkCutter.h>
#include <vtkOBBTree.h>
#include <vtkPlane.h>

SystematicPointPlanner* SystematicPointPlanner::m_instance = nullptr;

SystematicPointPlanner* SystematicPointPlanner::getInstance()
{
    if (m_instance == nullptr)
        m_instance = new SystematicPointPlanner();
    return m_instance;
}

SystematicPointPlanner::SystematicPointPlanner()
{
}

const std::vector<QVector3D> SystematicPointPlanner::planSystematicPoints(SystematicPointsPlanType type, vtkPolyData* modelPolyData, double* bounds)
{
    std::vector<QVector3D> points;
    switch (type)
    {
    case TWELVE_CORES:
        points = twelveCores(modelPolyData, bounds);
        break;
    // case TWENTYFOUR_CORES:
    //     points = twentyFourCores(modelPolyData, bounds);
    //     break;
    default:
        break;
    }
    return points;
}

const std::vector<QVector3D> SystematicPointPlanner::twelveCores(vtkSmartPointer<vtkPolyData> modelPolyData, double* bounds)
{
    // calculate the ylines
    std::vector<double> ratios = { 1.0 / 6, 6.0 / 18, 10.0 / 18, 15.0 / 18 };
    std::vector<double> yLines = getInterpolationLines(bounds[2], bounds[3], ratios);

    // calculate the intersection points
    std::map<int, std::vector<QVector3D>> intersectPointsMap = getModelLineIntersectionPoints(modelPolyData, bounds, yLines);

    // calculate the cores
    std::vector<QVector3D> cores;
    std::vector<QVector3D> tempCores;
    for (int i = 0; i < yLines.size(); i++)
    {
        std::vector<QVector3D> intersectPointInLine;
        intersectPointInLine = intersectPointsMap[i];
        if (intersectPointInLine.size() == 2)
        {
            QVector3D p1 = intersectPointInLine[0];
            QVector3D p2 = intersectPointInLine[1];
            if (i == 0)
                tempCores = twoCoresInbetween(p1, p2);
            else if (i == 1)
                tempCores = twoCoresInbetween(p1, p2, 7);
            else
                tempCores = fourCoresInbetween(p1, p2);
            cores.insert(cores.end(), tempCores.begin(), tempCores.end());
        }
        else if (intersectPointInLine.size() == 4)
        {
            QVector3D p1 = intersectPointInLine[0];
            QVector3D p2 = intersectPointInLine[1];
            QVector3D p3 = intersectPointInLine[2];
            QVector3D p4 = intersectPointInLine[3];
            std::vector<QVector3D> left = twoCoresInbetween(p1, p2);
            std::vector<QVector3D> right = twoCoresInbetween(p3, p4);
            cores.insert(cores.end(), left.begin(), left.end());
            cores.insert(cores.end(), right.begin(), right.end());
        }
        else
        {
            qDebug() << "Intersect points size is not 4 or 2, not supported yet.";
        }
    }
    return cores;
}

const std::vector<QVector3D> SystematicPointPlanner::twentyFourCores(vtkSmartPointer<vtkPolyData> modelPolyData, double* bounds)
{
    std::vector<QVector3D> cores;
    // calculate 3 contours
    double z1, z2, z3;
    z1 = bounds[4] + (bounds[5] - bounds[4]) * 1 / 6;
    z2 = bounds[4] + (bounds[5] - bounds[4]) * 3 / 6;
    z3 = bounds[4] + (bounds[5] - bounds[4]) * 5 / 6;

    // base 4+4 = 8

    std::pair<QVector3D, QVector3D> baseBounds = getCutContourBoundsAsPoints(modelPolyData, z1);
    std::vector<double> baseRatios = { 1.0 / 6, 2.0 / 6, 4.0 / 6, 5.0 / 6 };
    std::vector<double> baseYLines = getInterpolationLines(baseBounds.first.y(), baseBounds.second.y(), baseRatios);
    std::map<int, std::vector<QVector3D>> intersectPointsMap = getModelLineIntersectionPoints(modelPolyData, bounds, baseYLines);

    // mid 5+5 = 10
    // apex 3+3 = 6
    return cores;
}

const std::map<int, std::vector<QVector3D>> SystematicPointPlanner::getModelLineIntersectionPoints(vtkSmartPointer<vtkPolyData> modelPolyData, double* bounds, std::vector<double> lines)
{
    std::map<int, std::vector<QVector3D>> intersectPointsMap;
    vtkSmartPointer<vtkOBBTree> tree = vtkSmartPointer<vtkOBBTree>::New();
    tree->SetDataSet(modelPolyData);
    tree->BuildLocator();
    double tol = 1.e-3;
    tree->SetTolerance(tol);

    double xRange = bounds[1] - bounds[0];
    double zMid = (bounds[4] + bounds[5]) / 2;
    vtkSmartPointer<vtkPoints> intersectPoints = vtkSmartPointer<vtkPoints>::New();
    vtkSmartPointer<vtkIdList> intersectCells = vtkSmartPointer<vtkIdList>::New();

    for (int i = 0; i < lines.size(); i++)
    {
        double p1[3] = { bounds[0] - xRange * 0.2, lines[i], zMid };
        double p2[3] = { bounds[1] + xRange * 0.2, lines[i], zMid };

        tree->IntersectWithLine(p1, p2, intersectPoints, intersectCells);
        std::vector<QVector3D> tempPoints;
        for (int j = 0; j < intersectPoints->GetNumberOfPoints(); j++)
        {
            double* p = intersectPoints->GetPoint(j);
            QVector3D point(p[0], p[1], p[2]);
            tempPoints.push_back(point);
        }
        intersectPointsMap.insert_or_assign(i, tempPoints);
    }
    return intersectPointsMap;
}

const std::vector<double> SystematicPointPlanner::getInterpolationLines(double minValue, double maxValue, std::vector<double> ratios)
{
    std::vector<double> lines;
    for (int i = 0; i < ratios.size(); i++)
        lines.push_back(minValue + (maxValue - minValue) * ratios[i]);
    return lines;
}

const std::pair<QVector3D, QVector3D> SystematicPointPlanner::getCutContourBoundsAsPoints(vtkSmartPointer<vtkPolyData> modelPolyData, double zline)
{
    std::pair<QVector3D, QVector3D> points;
    vtkSmartPointer<vtkPlane> plane1 = vtkSmartPointer<vtkPlane>::New();
    plane1->SetOrigin(0, 0, zline);
    plane1->SetNormal(0, 0, 1);
    vtkSmartPointer<vtkCutter> cutter1 = vtkSmartPointer<vtkCutter>::New();
    cutter1->SetInputData(modelPolyData);
    cutter1->SetCutFunction(plane1);
    cutter1->Update();
    vtkSmartPointer<vtkPolyData> contour1 = cutter1->GetOutput();
    double* bounds = contour1->GetBounds();
    QVector3D p1(bounds[0], bounds[2], bounds[4]);
    QVector3D p2(bounds[1], bounds[4], bounds[5]);
    points.first = p1;
    points.second = p2;
    return points;
}

const std::vector<QVector3D> SystematicPointPlanner::twoCoresInbetween(QVector3D& firstPoint, QVector3D& secondPoint, int nSection)
{
    if (firstPoint.isNull() || secondPoint.isNull())
        return std::vector<QVector3D>();
    std::vector<QVector3D> cores;

    cores.push_back(firstPoint + (secondPoint - firstPoint) / nSection);
    cores.push_back(firstPoint + (secondPoint - firstPoint) * (nSection - 1) / nSection);
    return cores;
}

const std::vector<QVector3D> SystematicPointPlanner::fourCoresInbetween(QVector3D& firstPoint, QVector3D& secondPoint)
{
    if (firstPoint.isNull() || secondPoint.isNull())
        return std::vector<QVector3D>();

    std::vector<QVector3D> cores;
    cores.push_back(firstPoint + (secondPoint - firstPoint) / 8);
    cores.push_back(firstPoint + (secondPoint - firstPoint) * 3 / 8);
    cores.push_back(firstPoint + (secondPoint - firstPoint) * 5 / 8);
    cores.push_back(firstPoint + (secondPoint - firstPoint) * 7 / 8);
    return cores;
}