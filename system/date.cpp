#include <iostream>
#include <chrono>
#include <iomanip>

int main() {
    // Get current time
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    std::tm tm = *std::localtime(&time_t);
    
    // Format date as YYYYMMDD-HHMMSS and output
    std::cout << std::put_time(&tm, "%Y%m%d-%H%M%S");
    
    return 0;
}