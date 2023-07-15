#include <cstdlib>
#include <iostream>

#include <chrono/ChVersion.h>
#include <chrono/core/ChLog.h>
#include <chrono/core/ChVector.h>


int main(void) {
    std::cout << "Chrono version: " << CHRONO_VERSION << std::endl;
    chrono::GetLog() << "Hello world from ChronoEngine!" << "\n";
    chrono::ChVector<> mvect2;
    return EXIT_SUCCESS;
}
