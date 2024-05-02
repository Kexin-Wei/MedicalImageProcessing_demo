#pragma once

#include <QFileInfo>
#include <QVector3D>

#include <vtkActor.h>
#include <vtkAutoInit.h>
#include <vtkRenderWindow.h>
#include <vtkRenderer.h>
#include <vtkSTLReader.h>
#include <vtkSmartPointer.h>

VTK_MODULE_INIT(vtkRenderingOpenGL2);

enum SystematicPointsPlanType
{

    TWELVE_CORES,
    TWENTYFOUR_CORES
};

class SystematicPointPlanner
{
public:
    static SystematicPointPlanner* getInstance();
    ~SystematicPointPlanner();
    const std::vector<QVector3D> planSystematicPoints(SystematicPointsPlanType type, vtkPolyData* modelPolyData, double* bounds);

private:
    SystematicPointPlanner();
    const std::vector<QVector3D> twelveCores(vtkSmartPointer<vtkPolyData> modelPolyData, double* bounds);
    const std::vector<QVector3D> twentyFourCores(vtkSmartPointer<vtkPolyData> modelPolyData, double* bounds);

    const QVector3D oneCoreInbetween(QVector3D& firstPoint, QVector3D& secondPoint);
    const std::vector<QVector3D> twoCoresInbetween(QVector3D& firstPoint, QVector3D& secondPoint, int nSection = 6);
    const std::vector<QVector3D> fourCoresInbetween(QVector3D& firstPoint, QVector3D& secondPoint, std::vector<double> ratios);

    const std::pair<QVector3D, QVector3D> getCutContourBoundsAsPoints(vtkSmartPointer<vtkPolyData> modelPolyData, double zline);
    const std::map<int, std::vector<QVector3D>> getModelLineIntersectionPoints(vtkSmartPointer<vtkPolyData> modelPolyData, std::vector<std::pair<QVector3D, QVector3D>> linePoints);

    void convertQVectorToDouble(QVector3D& qVector, double* doubleArray);
    static SystematicPointPlanner* m_instance;
};