// #define BOX_METHOD
#define NEW_METHOD

#include <iostream>
#include <string>

#include <QDebug>
#include <QDir>
#include <QFileInfo>
#include <QFileInfoList>

#include <vtkPNGWriter.h>
#include <vtkWindowToImageFilter.h>

#ifdef BOX_METHOD
#include "SystematicPointPlanner.h"
#else
#ifdef NEW_METHOD
#include "SystematicPointPlanner3.h"
#include <vtkAxesActor.h>
#include <vtkCamera.h>
#include <vtkOrientationMarkerWidget.h>
#include <vtkPolyDataMapper.h>
#include <vtkProperty.h>
#include <vtkRenderWindowInteractor.h>
#include <vtkTransform.h>
#include <vtkTransformPolyDataFilter.h>

#else
#include "SystematicPointPlanner2.h"
#endif
#endif

void saveWindowToImage(QString& imgFileName, vtkSmartPointer<vtkRenderWindow> renderWindow)
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

void main()
{
#ifdef BOX_METHOD
    SystematicPointPlannerWithBox* spp = SystematicPointPlannerWithBox::getInstance();

    QDir folderPath = QString("D:/GitRepos/ITKMedicalImageProcessing_demo/data/biopsy-plan");
    QFileInfoList files = folderPath.entryInfoList();
    for (auto file : files)
    {
        if (file.isFile() && file.baseName().toLower().contains("t2"))
        {
            spp->setModelStlFileName(file.absoluteFilePath());
            spp->planSystematicPoints(SystematicPointsPlanType::TEN_CORES);
            spp->planSystematicPoints(SystematicPointsPlanType::TWELVE_CORESS);
        }
    }
#else
#ifdef NEW_METHOD
    SystematicPointsPlanType type = SystematicPointsPlanType::TWENTYFOUR_CORES;
    SystematicPointPlanner* spp = SystematicPointPlanner::getInstance();
    QDir folderPath = QString("D:/GitRepos/ITKMedicalImageProcessing_demo/data/biopsy-plan");
    QString saveImgPath = QString("D:/GitRepos/ITKMedicalImageProcessing_demo/result/biopsy-plan/new-boundary");
    QFileInfoList files = folderPath.entryInfoList();
    QString specimenFileName = "specimen_16g.STL";
    QFileInfo specimenFile = QFileInfo(folderPath.absoluteFilePath(specimenFileName));
    for (auto file : files)
    {
        if (file.isFile() && file.baseName().toLower().contains("seg"))
        {
            vtkSmartPointer<vtkSTLReader> reader = vtkSmartPointer<vtkSTLReader>::New();
            reader->SetFileName(file.absoluteFilePath().toStdString().c_str());
            reader->Update();

            vtkSmartPointer<vtkPolyDataMapper> mapper = vtkSmartPointer<vtkPolyDataMapper>::New();
            mapper->SetInputConnection(reader->GetOutputPort());
            vtkSmartPointer<vtkActor> actor = vtkSmartPointer<vtkActor>::New();
            actor->SetMapper(mapper);
            actor->GetProperty()->SetColor(1, 0, 0);
            actor->GetProperty()->SetOpacity(0.5);

            vtkSmartPointer<vtkRenderer> renderer = vtkSmartPointer<vtkRenderer>::New();
            renderer->AddActor(actor);
            std::vector<QVector3D> points = spp->planSystematicPoints(type, reader->GetOutput(), actor->GetBounds());

            vtkSmartPointer<vtkSTLReader> specimenReader = vtkSmartPointer<vtkSTLReader>::New();
            specimenReader->SetFileName(specimenFile.absoluteFilePath().toStdString().c_str());
            specimenReader->Update();

            for (auto point : points)
            {
                vtkSmartPointer<vtkTransform> transform = vtkSmartPointer<vtkTransform>::New();
                transform->Translate(point.x(), point.y(), point.z());

                vtkSmartPointer<vtkTransformPolyDataFilter> transformFilter = vtkSmartPointer<vtkTransformPolyDataFilter>::New();
                transformFilter->SetInputConnection(specimenReader->GetOutputPort());
                transformFilter->SetTransform(transform);
                transformFilter->Update();

                vtkSmartPointer<vtkPolyDataMapper> specimenMapper = vtkSmartPointer<vtkPolyDataMapper>::New();
                specimenMapper->SetInputConnection(transformFilter->GetOutputPort());
                vtkSmartPointer<vtkActor> specimenActor = vtkSmartPointer<vtkActor>::New();
                specimenActor->SetMapper(specimenMapper);
                specimenActor->GetProperty()->SetColor(0, 0, 1);
                renderer->AddActor(specimenActor);
            }

            vtkSmartPointer<vtkRenderWindow> renderWindow = vtkSmartPointer<vtkRenderWindow>::New();
            renderWindow->AddRenderer(renderer);
            renderWindow->SetSize(800, 800);
            vtkSmartPointer<vtkRenderWindowInteractor> renderWindowInteractor = vtkSmartPointer<vtkRenderWindowInteractor>::New();
            renderWindowInteractor->SetRenderWindow(renderWindow);

            vtkSmartPointer<vtkAxesActor> axes = vtkSmartPointer<vtkAxesActor>::New();
            axes->SetShaftTypeToCylinder();
            axes->SetXAxisLabelText("X");
            axes->SetYAxisLabelText("Y");
            axes->SetZAxisLabelText("Z");
            axes->SetTotalLength(1.0, 1.0, 1.0);
            axes->SetCylinderRadius(0.5 * axes->GetCylinderRadius());
            axes->SetConeRadius(1.025 * axes->GetConeRadius());
            axes->SetSphereRadius(1.5 * axes->GetSphereRadius());

            vtkSmartPointer<vtkOrientationMarkerWidget> widget = vtkSmartPointer<vtkOrientationMarkerWidget>::New();
            widget->SetOutlineColor(0.9300, 0.5700, 0.1300);
            widget->SetOrientationMarker(axes);
            widget->SetInteractor(renderWindowInteractor);
            widget->SetViewport(0.0, 0.0, 0.3, 0.3);
            widget->SetEnabled(1);
            widget->InteractiveOn();

            renderer->GetActiveCamera()->SetPosition(1, 0, 0);
            renderer->GetActiveCamera()->SetFocalPoint(0, 0, 0);
            renderer->GetActiveCamera()->SetViewUp(0, -1, 0);
            renderer->GetActiveCamera()->Azimuth(-90);
            renderer->ResetCamera();
            renderWindow->Render();

            QString typeName = type == SystematicPointsPlanType::TWELVE_CORES ? "twelve_core" : "twentyfour_core";
            QString imgFile = QString(saveImgPath) + QDir::separator() + typeName + "_" + file.baseName() + ".png";
            saveWindowToImage(imgFile, renderWindow);

            renderWindowInteractor->Initialize();
            renderWindowInteractor->Start();
        }
    }
#else

    SystematicPointPlannerTenTwelve* spp = SystematicPointPlannerTenTwelve::getInstance();

    QDir folderPath = QString("D:/GitRepos/ITKMedicalImageProcessing_demo/data/biopsy-plan");
    QFileInfoList files = folderPath.entryInfoList();
    for (auto file : files)
    {
        if (file.isFile() && file.baseName().toLower().contains("t2"))
        {
            spp->setModelStlFileName(file.absoluteFilePath());
            spp->planSystematicPoints(SystematicPointsPlanType::TEN_CORES);
            spp->planSystematicPoints(SystematicPointsPlanType::TWELVE_CORES);
        }
    }
#endif
#endif
}