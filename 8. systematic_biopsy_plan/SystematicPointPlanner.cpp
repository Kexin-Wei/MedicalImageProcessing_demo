#include "SystematicPointPlanner.h"

#include <QDebug>
#include <QDir>

#include <vtkPNGWriter.h>
#include <vtkPolyDataMapper.h>
#include <vtkProperty.h>
#include <vtkRenderWindowInteractor.h>
#include <vtkRenderer.h>
#include <vtkTransform.h>
#include <vtkTransformPolyDataFilter.h>
#include <vtkWindowToImageFilter.h>

SystematicPointPlannerWithBox* SystematicPointPlannerWithBox::m_instance = nullptr;

SystematicPointPlannerWithBox* SystematicPointPlannerWithBox::getInstance()
{
    if (m_instance == nullptr)
        m_instance = new SystematicPointPlannerWithBox();
    return m_instance;
}

SystematicPointPlannerWithBox::SystematicPointPlannerWithBox()
{
    QFileInfo folderPath = QString("D:/GitRepos/ITKMedicalImageProcessing_demo/data/biopsy-plan");
    QString modelFileName = "MainMR_AxT2_seg.stl";
    QString specimenFileName = "specimen_16g.STL";
    m_modelStlFile = QFileInfo(folderPath.absoluteFilePath() + QDir::separator() + modelFileName);
    m_specimenStlFile = QFileInfo(folderPath.absoluteFilePath() + QDir::separator() + specimenFileName);
}

void SystematicPointPlannerWithBox::setModelStlFileName(QString fileName)
{
    m_modelStlFile = QFileInfo(fileName);
}

void SystematicPointPlannerWithBox::planSystematicPoints(SystematicPointsPlanType type)
{
    if (!m_modelStlFile.exists())
    {
        qDebug() << "Model file not found";
        return;
    }

    vtkSmartPointer<vtkSTLReader> modelReader = vtkSmartPointer<vtkSTLReader>::New();
    modelReader->SetFileName(m_modelStlFile.absoluteFilePath().toStdString().c_str());
    modelReader->Update();

    vtkSmartPointer<vtkPolyDataMapper> modelMapper = vtkSmartPointer<vtkPolyDataMapper>::New();
    modelMapper->SetInputConnection(modelReader->GetOutputPort());
    vtkSmartPointer<vtkActor> modelActor = vtkSmartPointer<vtkActor>::New();
    modelActor->SetMapper(modelMapper);
    modelActor->GetProperty()->SetColor(1, 0, 0);
    modelActor->GetProperty()->SetOpacity(0.5);

    m_modelBounds = modelActor->GetBounds();
    getDiagnoalPointsFromBounds();

    m_renderer = vtkSmartPointer<vtkRenderer>::New();
    m_renderer->AddActor(modelActor);
    std::vector<vtkSmartPointer<vtkActor>> specimenActors = generateActorFromCores(type);
    for (auto actor : specimenActors)
        m_renderer->AddActor(actor);

    vtkSmartPointer<vtkRenderWindow> renderWindow = vtkSmartPointer<vtkRenderWindow>::New();
    renderWindow->AddRenderer(m_renderer);
    renderWindow->SetSize(800, 800);
    vtkSmartPointer<vtkRenderWindowInteractor> renderWindowInteractor = vtkSmartPointer<vtkRenderWindowInteractor>::New();
    renderWindowInteractor->SetRenderWindow(renderWindow);

    renderWindow->Render();

    QString typeName = type == SystematicPointsPlanType::TEN_CORES ? "ten_core" : "twelve_core";
    QString imgFile = QString("D:/GitRepos/ITKMedicalImageProcessing_demo/result/biopsy-plan") + QDir::separator() + typeName + "_" + m_modelStlFile.baseName() + ".png";
    saveWindowToImage(imgFile, renderWindow);

    renderWindowInteractor->Initialize();
    renderWindowInteractor->Start();
}

void SystematicPointPlannerWithBox::saveWindowToImage(QString& imgFileName, vtkSmartPointer<vtkRenderWindow> renderWindow)
{
    QFileInfo imgFileInfo(imgFileName);
    if (!imgFileInfo.absoluteDir().exists())
    {
        qDebug() << "Image file save folder is not found";
        return;
    }
    if (imgFileInfo.completeSuffix() != "png")
    {
        qDebug() << "Image file format not supported";
        return;
    }
    vtkSmartPointer<vtkPNGWriter> writer = vtkSmartPointer<vtkPNGWriter>::New();
    vtkSmartPointer<vtkWindowToImageFilter> windowToImageFilter = vtkSmartPointer<vtkWindowToImageFilter>::New();
    windowToImageFilter->SetInput(renderWindow);
    windowToImageFilter->SetScale(1);
    windowToImageFilter->SetInputBufferTypeToRGB();
    windowToImageFilter->ReadFrontBufferOff();
    windowToImageFilter->Update();

    writer->SetFileName(imgFileName.toStdString().c_str());
    writer->SetInputConnection(windowToImageFilter->GetOutputPort());
    writer->Write();
}

void SystematicPointPlannerWithBox::getDiagnoalPointsFromBounds()
{
    float midZ = (m_modelBounds[4] + m_modelBounds[5]) / 2;
    QVector3D p1, p3;
    p1.setX(m_modelBounds[0]);
    p1.setY(m_modelBounds[2]);
    p1.setZ(midZ);
    p3.setX(m_modelBounds[1]);
    p3.setY(m_modelBounds[3]);
    p3.setZ(midZ);

    m_diagonalPoints.first = p1;
    m_diagonalPoints.second = p3;
}

std::vector<vtkSmartPointer<vtkActor>> SystematicPointPlannerWithBox::generateActorFromCores(SystematicPointsPlanType type)
{
    std::vector<vtkSmartPointer<vtkActor>> specimenActors;
    std::vector<QVector3D> specimenCores;
    if (type == SystematicPointsPlanType::TEN_CORES)
        specimenCores = tenCores();
    else // type == SystematicPointsPlanType::TWELVE_CORESS)
        specimenCores = twelveCores();
    for (auto core : specimenCores)
        specimenActors.push_back(generateSpecimenActorFromPoint(core));
    return specimenActors;
}
vtkSmartPointer<vtkActor> SystematicPointPlannerWithBox::generateSpecimenActorFromPoint(QVector3D& p)
{
    if (!m_specimenStlFile.exists())
    {
        qDebug() << "Specimen file not found";
        return nullptr;
    }

    if (m_specimenReader == nullptr)
    {
        m_specimenReader = vtkSmartPointer<vtkSTLReader>::New();
        m_specimenReader->SetFileName(m_specimenStlFile.absoluteFilePath().toStdString().c_str());
        m_specimenReader->Update();
    }
    vtkSmartPointer<vtkTransform> transform = vtkSmartPointer<vtkTransform>::New();
    transform->Translate(p.x(), p.y(), p.z());

    vtkSmartPointer<vtkTransformPolyDataFilter> transformFilter = vtkSmartPointer<vtkTransformPolyDataFilter>::New();
    transformFilter->SetInputConnection(m_specimenReader->GetOutputPort());
    transformFilter->SetTransform(transform);
    transformFilter->Update();

    vtkSmartPointer<vtkPolyDataMapper> specimenMapper = vtkSmartPointer<vtkPolyDataMapper>::New();
    specimenMapper->SetInputConnection(transformFilter->GetOutputPort());
    vtkSmartPointer<vtkActor> specimenActor = vtkSmartPointer<vtkActor>::New();
    specimenActor->SetMapper(specimenMapper);
    specimenActor->GetProperty()->SetColor(0, 0, 1);
    return specimenActor;
}

std::vector<QVector3D> SystematicPointPlannerWithBox::tenCores()
{
    if (m_diagonalPoints.first.isNull() || m_diagonalPoints.second.isNull())
        return std::vector<QVector3D>();
    std::vector<QVector3D> corners = getFourCornersFromDiagnolPoints(m_diagonalPoints.first, m_diagonalPoints.second);
    QVector3D p1 = corners[0];
    QVector3D p2 = corners[1];
    QVector3D p3 = corners[2];
    QVector3D p4 = corners[3];

    std::vector<QVector3D> cores;
    QVector3D pCenter = centerOfTwoPoints(p1, p3);

    // tops
    QVector3D pLeftTopCenter = centerOfTwoPoints(p1, pCenter);
    QVector3D pRightTopCenter = centerOfTwoPoints(p2, pCenter);
    cores.push_back(pLeftTopCenter);
    cores.push_back(pRightTopCenter);

    // bottoms
    QVector3D p14 = centerOfTwoPoints(p1, p4);
    QVector3D p34 = centerOfTwoPoints(p3, p4);
    std::vector<QVector3D> leftBottomCores = fourCudeCentersFromDiagnolPoints(p14, p34, true);
    std::vector<QVector3D> rightBottomCores = fourCudeCentersFromDiagnolPoints(pCenter, p3, false);
    cores.insert(cores.end(), leftBottomCores.begin(), leftBottomCores.end());
    cores.insert(cores.end(), rightBottomCores.begin(), rightBottomCores.end());
    return cores;
}

std::vector<QVector3D> SystematicPointPlannerWithBox::twelveCores()
{
    if (m_diagonalPoints.first.isNull() || m_diagonalPoints.second.isNull())
        return std::vector<QVector3D>();
    std::vector<QVector3D> corners = getFourCornersFromDiagnolPoints(m_diagonalPoints.first, m_diagonalPoints.second);
    QVector3D p1 = corners[0];
    QVector3D p2 = corners[1];
    QVector3D p3 = corners[2];
    QVector3D p4 = corners[3];

    std::vector<QVector3D> cores;
    QVector3D pCenter = centerOfTwoPoints(p1, p3);
    // tops
    QVector3D p12 = centerOfTwoPoints(p1, p2);
    QVector3D pLeftTopCenter = centerOfTwoPoints(p1, pCenter);
    cores.push_back(centerOfTwoPoints(p12, pLeftTopCenter));
    QVector3D p14 = centerOfTwoPoints(p1, p4);
    cores.push_back(fourtheCenterOfLater(p14, pLeftTopCenter));

    QVector3D pRightTopCenter = centerOfTwoPoints(p2, pCenter);
    cores.push_back(centerOfTwoPoints(p12, pRightTopCenter));
    QVector3D p23 = centerOfTwoPoints(p2, p3);
    cores.push_back(fourtheCenterOfLater(p23, pRightTopCenter));

    // bottoms
    QVector3D p34 = centerOfTwoPoints(p3, p4);
    std::vector<QVector3D> leftBottomCores = fourCudeCentersFromDiagnolPoints(p14, p34, true);
    std::vector<QVector3D> rightBottomCores = fourCudeCentersFromDiagnolPoints(pCenter, p3, false);
    cores.insert(cores.end(), leftBottomCores.begin(), leftBottomCores.end());
    cores.insert(cores.end(), rightBottomCores.begin(), rightBottomCores.end());
    return cores;
}

std::vector<QVector3D> SystematicPointPlannerWithBox::fourCudeCentersFromDiagnolPoints(QVector3D& firstDiagonalPoint, QVector3D& secondDiagonalPoint, const bool left)
{
    std::vector<QVector3D> centers;
    std::vector<QVector3D> corners = getFourCornersFromDiagnolPoints(firstDiagonalPoint, secondDiagonalPoint);
    QVector3D p1 = corners[0];
    QVector3D p2 = corners[1];
    QVector3D p3 = corners[2];
    QVector3D p4 = corners[3];

    QVector3D pCenter = centerOfTwoPoints(p1, p3);
    if (left)
    {
        centers.push_back(centerOfTwoPoints(p1, pCenter));
        centers.push_back(centerOfTwoPoints(p2, pCenter));
        centers.push_back(centerOfTwoPoints(p3, pCenter));
        centers.push_back(fourtheCenterOfLater(p4, pCenter));
    }
    else
    {
        centers.push_back(centerOfTwoPoints(p1, pCenter));
        centers.push_back(centerOfTwoPoints(p2, pCenter));
        centers.push_back(centerOfTwoPoints(p4, pCenter));
        centers.push_back(fourtheCenterOfLater(p3, pCenter));
    }
    return centers;
}

QVector3D SystematicPointPlannerWithBox::fourtheCenterOfLater(QVector3D& firstPoint, QVector3D& secondPoint)
{
    if (firstPoint.isNull() || secondPoint.isNull())
        return QVector3D();
    QVector3D center = (firstPoint + secondPoint) / 2;
    QVector3D fourthPoint = (center + secondPoint) / 2;
    return fourthPoint;
}

QVector3D SystematicPointPlannerWithBox::centerOfTwoPoints(QVector3D& firstDiagonalPoint, QVector3D& secondDiagonalPoint)
{
    if (firstDiagonalPoint.isNull() || secondDiagonalPoint.isNull())
        return QVector3D();
    return (firstDiagonalPoint + secondDiagonalPoint) / 2;
}

std::vector<QVector3D> SystematicPointPlannerWithBox::getFourCornersFromDiagnolPoints(QVector3D& firstDiagonalPoint, QVector3D& secondDiagonalPoint)
{
    if (firstDiagonalPoint.isNull() || secondDiagonalPoint.isNull())
        return std::vector<QVector3D>();

    float x1, x2, y1, y2, z1, z2;
    x1 = firstDiagonalPoint.x();
    x2 = secondDiagonalPoint.x();
    y1 = firstDiagonalPoint.y();
    y2 = secondDiagonalPoint.y();
    z1 = firstDiagonalPoint.z();
    z2 = secondDiagonalPoint.z();
    if (z1 != z2)
        qDebug() << "z1 != z2";
    QVector3D p1, p2, p3, p4;
    p1.setX(x1);
    p1.setY(y1);
    p1.setZ(z1);

    p2.setX(x2);
    p2.setY(y1);
    p2.setZ(z1);

    p3.setX(x2);
    p3.setY(y2);
    p3.setZ(z1);

    p4.setX(x1);
    p4.setY(y2);
    p4.setZ(z1);

    std::vector<QVector3D> corners;
    corners.push_back(p1);
    corners.push_back(p2);
    corners.push_back(p3);
    corners.push_back(p4);
    return corners;
}