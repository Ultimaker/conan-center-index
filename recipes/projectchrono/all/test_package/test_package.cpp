#include <cstdlib>
#include <iostream>

#include <chrono/ChVersion.h>
#include <chrono/core/ChLog.h>
#include <chrono/core/ChVector.h>
#include <chrono/core/ChGlobal.h>

int main(void) {
    std::cout << "Chrono version: " << CHRONO_VERSION << std::endl;
    chrono::GetLog() << "Hello world from ChronoEngine!" << "\n";
    chrono::GetLog() << "Chrono version: " << CHRONO_VERSION << "\n";
    chrono::GetLog() << "ChVector: " << chrono::ChVector<>(1, 2, 3) << "\n";
    chrono::GetLog() << "Data path: " << chrono::GetChronoDataPath() << "\n";
    return EXIT_SUCCESS;
}
