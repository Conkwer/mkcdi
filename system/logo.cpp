#include <iostream>
#include <fstream>
#include <vector>
#include <memory>
#include <cstdlib>
#include <cstring>
#include <stdexcept>

class LogoInjector {
public:
    static void Run(int argc, char* argv[]) {
        if (argc != 3) {
            PrintUsage(argv[0]);
            std::exit(EXIT_FAILURE);
        }

        const std::string imagePath = argv[1];
        const std::string ipBinPath = argv[2];

        try {
            InjectLogo(imagePath, ipBinPath);
            std::cout << "Logo injection completed successfully!" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "Error: " << e.what() << std::endl;
            std::exit(EXIT_FAILURE);
        }
    }

private:
    static void PrintUsage(const char* programName) {
        std::cout << "logo insert tool\n";
        std::cout << "Usage: " << programName << " <image.mr> <ip.bin>\n";
    }

    static void InjectLogo(const std::string& imagePath, const std::string& ipBinPath) {
        // Read the logo image
        auto logoData = ReadFile(imagePath);
        
        // Check size warning
        if (logoData.size() > 8192) {
            std::cout << "Warning: this image is larger than 8192 bytes and will corrupt "
                      << "a normal ip.bin, inserting anyway!\n";
        }

        // Open IP.BIN for writing (in binary mode, append to existing file)
        std::fstream ipBinFile(ipBinPath, std::ios::in | std::ios::out | std::ios::binary);
        if (!ipBinFile) {
            throw std::runtime_error("Failed to open IP.BIN file: " + ipBinPath);
        }

        // Seek to the logo position (0x3820)
        ipBinFile.seekp(0x3820);
        if (!ipBinFile) {
            throw std::runtime_error("Failed to seek to logo position in IP.BIN");
        }

        // Write the logo data
        ipBinFile.write(reinterpret_cast<const char*>(logoData.data()), 
                       static_cast<std::streamsize>(logoData.size()));
        
        if (!ipBinFile) {
            throw std::runtime_error("Failed to write logo data to IP.BIN");
        }

        // Files are automatically closed by destructors
    }

    static std::vector<uint8_t> ReadFile(const std::string& filename) {
        std::ifstream file(filename, std::ios::binary | std::ios::ate);
        if (!file) {
            throw std::runtime_error("Failed to open file: " + filename);
        }

        const std::streamsize fileSize = file.tellg();
        file.seekg(0, std::ios::beg);

        std::vector<uint8_t> buffer(fileSize);
        if (!file.read(reinterpret_cast<char*>(buffer.data()), fileSize)) {
            throw std::runtime_error("Failed to read file: " + filename);
        }

        return buffer;
    }
};

int main(int argc, char* argv[]) {
    LogoInjector::Run(argc, argv);
    return EXIT_SUCCESS;
}