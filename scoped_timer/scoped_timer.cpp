#include "scoped_timer.hpp"
#include <sstream>

namespace timings{
std::string join(const std::vector<std::string>& stacked_names, const std::string& sep)
{
    std::ostringstream ss;

    for (auto& s : stacked_names) {
        ss << s << sep;
    }

    std::string out = ss.str();
    out.pop_back();

    return out;
}
}
