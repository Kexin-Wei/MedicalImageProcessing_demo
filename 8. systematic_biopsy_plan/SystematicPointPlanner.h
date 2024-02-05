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
    TWELVE_CORES
};

class SystematicPointPlannerWithBox
{
public:
    static SystematicPointPlannerWithBox* getInstance();
    ~SystematicPointPlannerWithBox();
    void setModelStlFileName(QString fileName);
    void planSystematicPoints(SystematicPointsPlanType type);

private:
    SystematicPointPlannerWithBox();
    QVector3D centerOfTwoPoints(QVector3D& firstDiagonalPoint, QVector3D& secondDiagonalPoint);
    QVector3D fourtheCenterOfLater(QVector3D& firstDiagonalPoint, QVector3D& secondDiagonalPoint);
    std::vector<QVector3D> fourCudeCentersFromDiagnolPoints(QVector3D& firstDiagonalPoint, QVector3D& secondDiagonalPoint, const bool left);
    std::vector<QVector3D> getFourCornersFromDiagnolPoints(QVector3D& firstDiagonalPoint, QVector3D& secondDiagonalPoint);
    vtkSmartPointer<vtkActor> generateSpecimenActorFromPoint(QVector3D& p);
    std::vector<QVector3D> tenCores();
    std::vector<QVector3D> twelveCores();
    void getDiagnoalPointsFromBounds();
    void saveWindowToImage(QString& imgFileName, vtkSmartPointer<vtkRenderWindow> renderWindow);
    std::vector<vtkSmartPointer<vtkActor>> generateActorFromCores(SystematicPointsPlanType type);

    static SystematicPointPlannerWithBox* m_instance;
    QFileInfo m_modelStlFile;
    QFileInfo m_specimenStlFile;
    double* m_modelBounds;
    std::pair<QVector3D, QVector3D> m_diagonalPoints;
    vtkSmartPointer<vtkSTLReader> m_specimenReader;
    vtkSmartPointer<vtkRenderer> m_renderer;
};