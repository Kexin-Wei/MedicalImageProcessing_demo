// #define BOX_METHOD

#include <iostream>
#include <string>

#include <QDebug>
#include <QDir>
#include <QFileInfo>
#include <QFileInfoList>

#ifdef BOX_METHOD
#include "SystematicPointPlanner.h"
#else
#include "SystematicPointPlanner2.h"
#endif

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
    SystematicPointPlanner* spp = SystematicPointPlanner::getInstance();

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

#endif
}