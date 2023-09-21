#include "SystematicPointPlanner.h"
#include <iostream>
#include <string>

void main()
{
    SystematicPointPlanner* spp = SystematicPointPlanner::getInstance();
    spp->planSystematicPoints(SystematicPointsPlanType::TEN_CORES);
    spp->planSystematicPoints(SystematicPointsPlanType::TWELVE_CORESS);
    return;
}