#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <algorithm>
#include <filesystem>
#include <cstdint>
#include <getopt.h>

namespace fs = std::filesystem;

// Configuration structure
struct Config {
    uint32_t old_pos = 0xafc8;
    uint32_t new_pos = 0x2db6;
    bool hack0 = false;
    bool hack1 = false;
    bool hack2 = false;
    bool hack3 = false;
    bool unprotect = false;
    bool write_mode = false;
    bool show_help = false;
};

// Print usage information
void print_usage() {
    std::cout << "Usage: hack4 [options] target_file[s]\n";
    std::cout << "(You can use wild card in \"target_file[s]\")\n\n";
    std::cout << "\t-o: set old position. default: [45000]\n";
    std::cout << "\t-n: set new position. default: [11702]\n";
    std::cout << "\t-0: Act HACK0, (oldpos [45000] -> newpos [11702]) default: [disable]\n";
    std::cout << "\t-1: Act HACK1, (oldpos+166 [45166] -> newpos+166 [11868])\n";
    std::cout << "\t-2: Act HACK2, (oldpos+150 [45150] -> newpos+150 [11852])\n";
    std::cout << "\t-3: Act HACK3, (HACK1 + HACK2)\n";
    std::cout << "\t-p: Act unprotect mode (CD E4 43 6A -> 09 00 09 00) only.\n";
    std::cout << "\t-w: write mode. (BE CAREFUL!!)  default: [don't patch]\n";
    std::cout << "\t-h: show this help.\n";
}

// Parse command line arguments
Config parse_arguments(int argc, char* argv[]) {
    Config config;
    int opt;
    
    static struct option long_options[] = {
        {"old-pos", required_argument, 0, 'o'},
        {"new-pos", required_argument, 0, 'n'},
        {"hack0", no_argument, 0, '0'},
        {"hack1", no_argument, 0, '1'},
        {"hack2", no_argument, 0, '2'},
        {"hack3", no_argument, 0, '3'},
        {"unprotect", no_argument, 0, 'p'},
        {"write", no_argument, 0, 'w'},
        {"help", no_argument, 0, 'h'},
        {0, 0, 0, 0}
    };
    
    while ((opt = getopt_long(argc, argv, "o:n:0123pwh", long_options, NULL)) != -1) {
        switch (opt) {
            case 'o':
                config.old_pos = std::stoul(optarg, nullptr, 0);
                break;
            case 'n':
                config.new_pos = std::stoul(optarg, nullptr, 0);
                break;
            case '0':
                config.hack0 = true;
                break;
            case '1':
                config.hack1 = true;
                break;
            case '2':
                config.hack2 = true;
                break;
            case '3':
                config.hack3 = true;
                break;
            case 'p':
                config.unprotect = true;
                break;
            case 'w':
                config.write_mode = true;
                break;
            case 'h':
                config.show_help = true;
                break;
            default:
                print_usage();
                exit(EXIT_FAILURE);
        }
    }
    
    return config;
}

// Read file into a byte vector
std::vector<uint8_t> read_file(const std::string& filename) {
    std::ifstream file(filename, std::ios::binary | std::ios::ate);
    if (!file) {
        throw std::runtime_error("Cannot open file: " + filename);
    }
    
    std::streamsize size = file.tellg();
    file.seekg(0, std::ios::beg);
    
    std::vector<uint8_t> buffer(size);
    if (!file.read(reinterpret_cast<char*>(buffer.data()), size)) {
        throw std::runtime_error("Cannot read file: " + filename);
    }
    
    return buffer;
}

// Write byte vector to file
void write_file(const std::string& filename, const std::vector<uint8_t>& data) {
    std::ofstream file(filename, std::ios::binary);
    if (!file) {
        throw std::runtime_error("Cannot open file for writing: " + filename);
    }
    
    file.write(reinterpret_cast<const char*>(data.data()), data.size());
}

// Convert 4 bytes to a uint32_t (little-endian)
uint32_t bytes_to_uint32(const std::vector<uint8_t>& data, size_t offset) {
    return (data[offset + 3] << 24) | (data[offset + 2] << 16) | 
           (data[offset + 1] << 8) | data[offset];
}

// Convert uint32_t to 4 bytes (little-endian)
void uint32_to_bytes(std::vector<uint8_t>& data, size_t offset, uint32_t value) {
    data[offset] = value & 0xFF;
    data[offset + 1] = (value >> 8) & 0xFF;
    data[offset + 2] = (value >> 16) & 0xFF;
    data[offset + 3] = (value >> 24) & 0xFF;
}

// Check if a pattern exists at a specific position
bool check_pattern(const std::vector<uint8_t>& data, size_t offset, 
                  const std::vector<uint8_t>& pattern) {
    if (offset + pattern.size() > data.size()) {
        return false;
    }
    
    for (size_t i = 0; i < pattern.size(); i++) {
        if (data[offset + i] != pattern[i]) {
            return false;
        }
    }
    
    return true;
}

// Apply patches to the binary data
bool apply_patches(std::vector<uint8_t>& data, const Config& config) {
    bool patched = false;
    
    // Unprotect mode pattern: CD E4 43 6A -> 09 00 09 00
    const std::vector<uint8_t> unprotect_pattern = {0xCD, 0xE4, 0x43, 0x6A};
    const std::vector<uint8_t> unprotect_replace = {0x09, 0x00, 0x09, 0x00};
    
    // Search for the unprotect pattern
    if (config.unprotect) {
        for (size_t i = 0; i <= data.size() - unprotect_pattern.size(); i++) {
            if (check_pattern(data, i, unprotect_pattern)) {
                std::cout << "Found unprotect pattern at offset: 0x" << std::hex << i << std::dec << "\n";
                if (config.write_mode) {
                    std::copy(unprotect_replace.begin(), unprotect_replace.end(), data.begin() + i);
                    std::cout << "Applied unprotect patch\n";
                    patched = true;
                } else {
                    std::cout << "Would apply unprotect patch (use -w to write)\n";
                }
            }
        }
    }
    
    // HACK0: Direct position replacement
    if (config.hack0 || config.hack1 || config.hack2 || config.hack3) {
        // Search for the old position value
        for (size_t i = 0; i <= data.size() - 4; i++) {
            uint32_t value = bytes_to_uint32(data, i);
            
            if (value == config.old_pos) {
                std::cout << "Found old position at offset: 0x" << std::hex << i << std::dec << "\n";
                if (config.write_mode) {
                    uint32_to_bytes(data, i, config.new_pos);
                    std::cout << "Applied HACK0 patch\n";
                    patched = true;
                } else {
                    std::cout << "Would apply HACK0 patch (use -w to write)\n";
                }
            }
            
            // HACK1: oldpos + 166 -> newpos + 166
            if (config.hack1 || config.hack3) {
                if (value == config.old_pos + 166) {
                    std::cout << "Found old position + 166 at offset: 0x" << std::hex << i << std::dec << "\n";
                    if (config.write_mode) {
                        uint32_to_bytes(data, i, config.new_pos + 166);
                        std::cout << "Applied HACK1 patch\n";
                        patched = true;
                    } else {
                        std::cout << "Would apply HACK1 patch (use -w to write)\n";
                    }
                }
            }
            
            // HACK2: oldpos + 150 -> newpos + 150
            if (config.hack2 || config.hack3) {
                if (value == config.old_pos + 150) {
                    std::cout << "Found old position + 150 at offset: 0x" << std::hex << i << std::dec << "\n";
                    if (config.write_mode) {
                        uint32_to_bytes(data, i, config.new_pos + 150);
                        std::cout << "Applied HACK2 patch\n";
                        patched = true;
                    } else {
                        std::cout << "Would apply HACK2 patch (use -w to write)\n";
                    }
                }
            }
        }
    }
    
    return patched;
}

// Process a single file
void process_file(const std::string& filename, const Config& config) {
    try {
        std::cout << "Processing: " << filename << "\n";
        
        // Read the file
        auto data = read_file(filename);
        
        // Apply patches
        bool patched = apply_patches(data, config);
        
        // Write back if in write mode and patches were applied
        if (config.write_mode && patched) {
            write_file(filename, data);
            std::cout << "Successfully patched: " << filename << "\n";
        }
        
        std::cout << "Finished: " << filename << "\n\n";
    } catch (const std::exception& e) {
        std::cerr << "Error processing " << filename << ": " << e.what() << "\n";
    }
}

// Expand wildcard pattern to matching files
std::vector<std::string> expand_wildcard(const std::string& pattern) {
    std::vector<std::string> files;
    
    try {
        fs::path path(pattern);
        std::string dir = path.parent_path().string();
        std::string filename_pattern = path.filename().string();
        
        if (dir.empty()) dir = ".";
        
        for (const auto& entry : fs::directory_iterator(dir)) {
            if (entry.is_regular_file()) {
                std::string filename = entry.path().filename().string();
                
                // Simple wildcard matching (supports * only)
                if (filename_pattern == "*" || 
                    filename_pattern.find('*') != std::string::npos) {
                    std::string pattern_regex = filename_pattern;
                    size_t pos = pattern_regex.find('*');
                    while (pos != std::string::npos) {
                        pattern_regex.replace(pos, 1, ".*");
                        pos = pattern_regex.find('*', pos + 2);
                    }
                    
                    // Simple matching for demonstration
                    // In a real implementation, you'd use proper regex
                    if (filename_pattern == "*" || 
                        filename.find(filename_pattern.substr(0, filename_pattern.find('*'))) != std::string::npos) {
                        files.push_back(entry.path().string());
                    }
                } else if (filename == filename_pattern) {
                    files.push_back(entry.path().string());
                }
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "Error expanding wildcard: " << e.what() << "\n";
    }
    
    return files;
}

int main(int argc, char* argv[]) {
    std::cout << "*** hack4 (Modern C++ Implementation) ***\n";
    std::cout << "Dreamcast Binary Patcher Tool\n\n";
    
    // Parse command line arguments
    Config config = parse_arguments(argc, argv);
    
    if (config.show_help || argc == 1) {
        print_usage();
        return 0;
    }
    
    // Get target files from command line
    std::vector<std::string> target_files;
    for (int i = optind; i < argc; i++) {
        std::string arg = argv[i];
        
        // Check if argument contains wildcard
        if (arg.find('*') != std::string::npos) {
            auto expanded = expand_wildcard(arg);
            target_files.insert(target_files.end(), expanded.begin(), expanded.end());
        } else {
            target_files.push_back(arg);
        }
    }
    
    if (target_files.empty()) {
        std::cerr << "Error: No target files specified\n";
        print_usage();
        return 1;
    }
    
    // Process each file
    for (const auto& file : target_files) {
        process_file(file, config);
    }
    
    std::cout << "Processing complete.\n";
    return 0;
}