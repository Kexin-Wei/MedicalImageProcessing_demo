#include "SystematicPointPlanner2.h"

#include <QDebug>
#include <QDir>

#include <vtkCutter.h>
#include <vtkLineSource.h>
#include <vtkOBBTree.h>
#include <vtkPlane.h>
#include <vtkPoints.h>
#include <vtkPolygon.h>

#include <vtkPNGWriter.h>
#include <vtkPolyDataMapper.h>
#include <vtkProperty.h>
#include <vtkRenderWindowInteractor.h>
#include <vtkRenderer.h>
#include <vtkTransform.h>
#include <vtkTransformPolyDataFilter.h>
#include <vtkWindowToImageFilter.h>

SystematicPointPlanner* SystematicPointPlanner::m_instance = nullptr;

SystematicPointPlanner* SystematicPointPlanner::getInstance()
{
    if (m_instance == nullptr)
        m_instance = new SystematicPointPlanner();
    return m_instance;
}

SystematicPointPlanner::SystematicPointPlanner()
{
    QFileInfo folderPath = QString("D:/GitRepos/ITKMedicalImageProcessing_demo/data/biopsy-plan");
    QString modelFileName = "MainMR_AxT2_seg.stl";
    QString specimenFileName = "specimen_16g.STL";
    m_modelStlFile = QFileInfo(folderPath.absoluteFilePath() + QDir::separator() + modelFileName);
    m_specimenStlFile = QFileInfo(folderPath.absoluteFilePath() + QDir::separator() + specimenFileName);
}

void SystematicPointPlanner::setModelStlFileName(QString fileName)
{
    QFileInfo modelStlFile = QFileInfo(fileName);
    if (m_modelStlFile.suffix() != "stl")
    {
        qDebug() << "Invalid file type";
        return;
    }
    m_modelStlFile = modelStlFile;
}

void SystematicPointPlanner::planSystematicPoints(SystematicPointsPlanType type)
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

    getIntersectPointsCoord(modelReader->GetOutput(), modelActor->GetBounds(), type);

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
    QString imgFile = QString("D:/GitRepos/ITKMedicalImageProcessing_demo/result/biopsy-plan/boundary") + QDir::separator() + typeName + "_" + m_modelStlFile.baseName() + ".png";
    saveWindowToImage(imgFile, renderWindow);

    renderWindowInteractor->Initialize();
    renderWindowInteractor->Start();
}

void SystematicPointPlanner::saveWindowToImage(QString& imgFileName, vtkSmartPointer<vtkRenderWindow> renderWindow)
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

std::vector<QVector3D> SystematicPointPlanner::getIntersectLines(double* bounds, SystematicPointsPlanType type)
{
    double x1, x2, y1, y2, zMid, xMid;
    double xRange;
    zMid = (bounds[4] + bounds[5]) / 2;
    x1 = bounds[0];
    x2 = bounds[1];
    y1 = bounds[2];
    y2 = bounds[3];
    xMid = (x1 + x2) / 2;
    xRange = x2 - x1;

    std::vector<QVector3D> linePoints;
    std::vector<double> ylines;
    if (type == SystematicPointsPlanType::TEN_CORES)
    {
        m_nIntesectLine = 3;
        ylines.push_back(y1 + (y2 - y1) * 1 / 6);
        ylines.push_back(y1 + (y2 - y1) * 3 / 6);
        ylines.push_back(y1 + (y2 - y1) * 5 / 6);
    }
    else
    {
        m_nIntesectLine = 4;
        ylines.push_back(y1 + (y2 - y1) * 1 / 6);
        ylines.push_back(y1 + (y2 - y1) * 6 / 18);
        ylines.push_back(y1 + (y2 - y1) * 10 / 18);
        ylines.push_back(y1 + (y2 - y1) * 15 / 18);
    }

    for (int i = 0; i < m_nIntesectLine; i++)
    {
        QVector3D point1, point2;
        point1.setX(x1 - xRange * 0.2);
        point1.setY(ylines[i]);
        point1.setZ(zMid);
        point2.setX(x2 + xRange * 0.2);
        point2.setY(ylines[i]);
        point2.setZ(zMid);
        linePoints.push_back(point1);
        linePoints.push_back(point2);
    }
    return linePoints;
}

void SystematicPointPlanner::getIntersectPointsCoord(vtkPolyData* modelPolyData, double* bounds, SystematicPointsPlanType type)
{
    if (m_intersectPoints.size() > 0)
        m_intersectPoints.clear();

    std::vector<QVector3D> linePoints = getIntersectLines(bounds, type);

    vtkSmartPointer<vtkOBBTree> tree = vtkSmartPointer<vtkOBBTree>::New();
    tree->SetDataSet(modelPolyData);
    tree->BuildLocator();
    double tol = 1.e-3;
    tree->SetTolerance(tol);

    vtkSmartPointer<vtkPoints> intersectPoints = vtkSmartPointer<vtkPoints>::New();
    vtkSmartPointer<vtkIdList> intersectCells = vtkSmartPointer<vtkIdList>::New();

    for (int i = 0; i < linePoints.size() / 2; i++)
    {
        double p1[3] = { linePoints[i * 2].x(), linePoints[i * 2].y(), linePoints[i * 2].z() };
        double p2[3] = { linePoints[i * 2 + 1].x(), linePoints[i * 2 + 1].y(), linePoints[i * 2 + 1].z() };

        tree->IntersectWithLine(p1, p2, intersectPoints, intersectCells);
        if (intersectPoints->GetNumberOfPoints() > 2)
            qDebug() << "Intersect points number is more than 2, which is not supported yet";
        for (int j = 0; j < intersectPoints->GetNumberOfPoints(); j++)
        {
            double* p = intersectPoints->GetPoint(j);
            QVector3D point;
            point.setX(p[0]);
            point.setY(p[1]);
            point.setZ(p[2]);
            m_intersectPoints.push_back(point);
        }
    }
}

std::vector<vtkSmartPointer<vtkActor>> SystematicPointPlanner::generateActorFromCores(SystematicPointsPlanType type)
{
    std::vector<vtkSmartPointer<vtkActor>> specimenActors;
    if (type == SystematicPointsPlanType::TEN_CORES)
        tenCores();
    else // type == SystematicPointsPlanType::TWELVE_CORESS)
        twelveCores();
    for (auto core : m_cores)
        specimenActors.push_back(generateSpecimenActorFromPoint(core));
    return specimenActors;
}

vtkSmartPointer<vtkActor> SystematicPointPlanner::generateSpecimenActorFromPoint(QVector3D& p)
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

void SystematicPointPlanner::tenCores()
{
    if (m_cores.size() > 0)
        m_cores.clear();
    std::vector<QVector3D> tempCores;
    for (int i = 0; i < m_nIntesectLine; i++)
    {
        QVector3D p1 = m_intersectPoints[2 * i];
        QVector3D p2 = m_intersectPoints[2 * i + 1];
        if (i == 0)
        {
            tempCores = TwoCoresInbetween(p1, p2);
            m_cores.insert(m_cores.end(), tempCores.begin(), tempCores.end());
        }
        else
        {
            tempCores = FourCoresInbetween(p1, p2);
            m_cores.insert(m_cores.end(), tempCores.begin(), tempCores.end());
        }
    }
}

void SystematicPointPlanner::twelveCores()
{
    if (m_cores.size() > 0)
        m_cores.clear();
    std::vector<QVector3D> tempCores;
    for (int i = 0; i < m_nIntesectLine; i++)
    {
        QVector3D p1 = m_intersectPoints[2 * i];
        QVector3D p2 = m_intersectPoints[2 * i + 1];
        if (i == 0)
            tempCores = TwoCoresInbetween(p1, p2);
        else if (i == 1)
            tempCores = TwoCoresInbetween(p1, p2, 7);
        else
            tempCores = FourCoresInbetween(p1, p2);
        m_cores.insert(m_cores.end(), tempCores.begin(), tempCores.end());
    }
}

std::vector<QVector3D> SystematicPointPlanner::FourCoresInbetween(QVector3D& firstPoint, QVector3D& secondPoint)
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

std::vector<QVector3D> SystematicPointPlanner::TwoCoresInbetween(QVector3D& firstPoint, QVector3D& secondPoint, int nSection)
{
    if (firstPoint.isNull() || secondPoint.isNull())
        return std::vector<QVector3D>();
    std::vector<QVector3D> cores;

    cores.push_back(firstPoint + (secondPoint - firstPoint) / nSection);
    cores.push_back(firstPoint + (secondPoint - firstPoint) * (nSection - 1) / nSection);
    return cores;
}
