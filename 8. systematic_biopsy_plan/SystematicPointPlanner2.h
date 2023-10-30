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
    TEN_CORES,
    TWELVE_CORESS
};

class SystematicPointPlanner
{
public:
    static SystematicPointPlanner* getInstance();
    ~SystematicPointPlanner();
    void setModelStlFileName(QString fileName);
    void planSystematicPoints(SystematicPointsPlanType type);

private:
    SystematicPointPlanner();
    std::vector<QVector3D> TwoCoresInbetween(QVector3D& firstDiagonalPoint, QVector3D& secondDiagonalPoint, int nSection = 6);
    std::vector<QVector3D> FourCoresInbetween(QVector3D& firstDiagonalPoint, QVector3D& secondDiagonalPoint);
    vtkSmartPointer<vtkActor> generateSpecimenActorFromPoint(QVector3D& p);
    void tenCores();
    void twelveCores();
    std::vector<QVector3D> getIntersectLines(double* bounds, SystematicPointsPlanType type);
    void getIntersectPointsCoord(vtkPolyData* modelPolyData, double* bounds, SystematicPointsPlanType type);
    void saveWindowToImage(QString& imgFileName, vtkSmartPointer<vtkRenderWindow> renderWindow);
    std::vector<vtkSmartPointer<vtkActor>> generateActorFromCores(vtkPolyData* modelPolyData, double* bounds, SystematicPointsPlanType type);

    static SystematicPointPlanner* m_instance;
    QFileInfo m_modelStlFile;
    QFileInfo m_specimenStlFile;
    double* m_modelBounds;

    std::map<int, std::vector<QVector3D>> m_intersectPoints;
    std::vector<QVector3D> m_cores;
    int m_nIntesectLine;
    vtkSmartPointer<vtkSTLReader> m_specimenReader;
    vtkSmartPointer<vtkRenderer> m_renderer;
};