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
    case TWENTYFOUR_CORES:
        points = twentyFourCores(modelPolyData, bounds);
        break;
    default:
        break;
    }
    return points;
}

const std::vector<QVector3D> SystematicPointPlanner::twelveCores(vtkSmartPointer<vtkPolyData> modelPolyData, double* bounds)
{
    // calculate the lines
    std::vector<double> ratios = { 2.5 / 12, 3.0 / 6, 9.5 / 12 };

    double xRange = bounds[1] - bounds[0];
    double zMid = (bounds[4] + bounds[5]) / 2;
    std::vector<std::pair<QVector3D, QVector3D>> linePoints;
    for (int i = 0; i < ratios.size(); i++)
    {
        double yValue = bounds[2] + (bounds[3] - bounds[2]) * ratios[i];
        QVector3D p1(bounds[0] - xRange * ratios[i], yValue, zMid);
        QVector3D p2(bounds[1] + xRange * ratios[i], yValue, zMid);
        linePoints.push_back(std::make_pair(p1, p2));
    }

    // calculate the intersection points
    std::map<int, std::vector<QVector3D>> intersectPointsMap = getModelLineIntersectionPoints(modelPolyData, linePoints);

    // calculate the cores
    std::vector<QVector3D> cores;
    std::vector<QVector3D> tempCores;
    for (int i = 0; i < linePoints.size(); i++)
    {
        if (intersectPointsMap[i].size() == 2)
        {
            QVector3D p1 = intersectPointsMap[i][0];
            QVector3D p2 = intersectPointsMap[i][1];
            tempCores = fourCoresInbetween(p1, p2);
            cores.insert(cores.end(), tempCores.begin(), tempCores.end());
        }
        else if (intersectPointsMap[i].size() == 4)
        {
            QVector3D p1 = intersectPointsMap[i][0];
            QVector3D p2 = intersectPointsMap[i][1];
            QVector3D p3 = intersectPointsMap[i][2];
            QVector3D p4 = intersectPointsMap[i][3];
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
    double zMid = (bounds[4] + bounds[5]) / 2;
    double xRange = bounds[1] - bounds[0];
    double xMid = (bounds[0] + bounds[1]) / 2;

    std::vector<std::pair<double, double>> lineRatios = {
        { 6.0 / 12, 2.0 / 12 },
        { 7.0 / 12, 9.0 / 12 },
        { 9.0 / 12, 11.0 / 12 },
    };
    // left side lines
    std::vector<std::pair<QVector3D, QVector3D>> leftLinePoints;
    for (int i = 0; i < lineRatios.size(); i++)
    {
        double y1 = bounds[2] + (bounds[3] - bounds[2]) * lineRatios[i].first;
        double y2 = bounds[2] + (bounds[3] - bounds[2]) * lineRatios[i].second;
        QVector3D p1(bounds[0], y1, zMid);
        QVector3D p2(xMid, y2, zMid);
        leftLinePoints.push_back(std::make_pair(p1, p2));
    }

    // intersection points
    std::map<int, std::vector<QVector3D>> leftIntersectPointsMap = getModelLineIntersectionPoints(modelPolyData, leftLinePoints);

    // add the cores
    std::vector<QVector3D> leftTempCores;
    for (int i = 0; i < leftLinePoints.size(); i++)
    {
        QVector3D p1 = leftIntersectPointsMap[i][0];
        QVector3D p2 = leftLinePoints[i].second;
        leftTempCores = fourCoresInbetween(p1, p2);
        cores.insert(cores.end(), leftTempCores.begin(), leftTempCores.end());
    }

    // right side lines
    std::vector<std::pair<QVector3D, QVector3D>> rightLinePoints;
    for (int i = 0; i < lineRatios.size(); i++)
    {
        double y1 = bounds[2] + (bounds[3] - bounds[2]) * lineRatios[i].second;
        double y2 = bounds[2] + (bounds[3] - bounds[2]) * lineRatios[i].first;
        QVector3D p1(xMid, y1, zMid);
        QVector3D p2(bounds[1], y2, zMid);
        rightLinePoints.push_back(std::make_pair(p1, p2));
    }

    // intersection points
    std::map<int, std::vector<QVector3D>> rightleftIntersectPointsMap = getModelLineIntersectionPoints(modelPolyData, rightLinePoints);

    // add the cores
    std::vector<QVector3D> rightTempCores;
    for (int i = 0; i < leftLinePoints.size(); i++)
    {
        QVector3D p2 = rightLinePoints[i].first;
        QVector3D p1 = rightleftIntersectPointsMap[i][rightleftIntersectPointsMap[i].size() - 1];
        rightTempCores = fourCoresInbetween(p1, p2);
        cores.insert(cores.end(), rightTempCores.begin(), rightTempCores.end());
    }
    return cores;
}

const std::map<int, std::vector<QVector3D>> SystematicPointPlanner::getModelLineIntersectionPoints(vtkSmartPointer<vtkPolyData> modelPolyData, std::vector<std::pair<QVector3D, QVector3D>> linePoints)
{
    std::map<int, std::vector<QVector3D>> intersectPointsMap;
    vtkSmartPointer<vtkOBBTree> tree = vtkSmartPointer<vtkOBBTree>::New();
    tree->SetDataSet(modelPolyData);
    tree->BuildLocator();
    double tol = 1.e-3;
    tree->SetTolerance(tol);

    vtkSmartPointer<vtkPoints> intersectPoints = vtkSmartPointer<vtkPoints>::New();
    vtkSmartPointer<vtkIdList> intersectCells = vtkSmartPointer<vtkIdList>::New();

    for (int i = 0; i < linePoints.size(); i++)
    {
        double p1[3], p2[3];
        convertQVectorToDouble(linePoints[i].first, p1);
        convertQVectorToDouble(linePoints[i].second, p2);
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

const QVector3D SystematicPointPlanner::oneCoreInbetween(QVector3D& firstPoint, QVector3D& secondPoint)
{
    if (firstPoint.isNull() || secondPoint.isNull())
        return QVector3D();
    return (firstPoint + secondPoint) / 2;
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
    cores.push_back(firstPoint + (secondPoint - firstPoint) / 5);
    cores.push_back(firstPoint + (secondPoint - firstPoint) * 2 / 5);
    cores.push_back(firstPoint + (secondPoint - firstPoint) * 3 / 5);
    cores.push_back(firstPoint + (secondPoint - firstPoint) * 4 / 5);
    return cores;
}

void SystematicPointPlanner::convertQVectorToDouble(QVector3D& qVector, double* doubleArray)
{
    doubleArray[0] = qVector.x();
    doubleArray[1] = qVector.y();
    doubleArray[2] = qVector.z();
}