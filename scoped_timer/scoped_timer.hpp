//! \file
//! \brief scoped timer
//!
//! This file contains a scoped timer class that can be used to measure the time
//! spent in a scope.
//! It supports nesting of scopes and can print the timings of all scopes at the
//! end of the program.
//!
//! Example usage:
//! \code
//! {
//!     default_scoped_timer t("my scope");
//!     // do stuff
//! }
//! default_scoped_timer::print_timings();
//! \endcode
//!

#pragma once

#include <chrono>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <algorithm>
#include <sstream>
#include <string>
#include <vector>

namespace timings{

enum class unit { ms, us, ns };

// clang-format off
template<unit U> struct unit_to_chrono_unit;
template<> struct unit_to_chrono_unit<unit::ms> { using type = std::chrono::milliseconds; constexpr static char str[] = "ms";};
template<> struct unit_to_chrono_unit<unit::us> { using type = std::chrono::microseconds; constexpr static char str[] = "us";};
template<> struct unit_to_chrono_unit<unit::ns> { using type = std::chrono::nanoseconds; constexpr static char str[] = "ns";};
// clang-format on

struct timing_session {
    std::vector<unsigned int> timings;
};

std::string join(const std::vector<std::string>& stacked_names, const std::string& sep);

template <unit U> class scoped_timer {
    std::chrono::high_resolution_clock::time_point before;
    std::string name;
    std::string fullname;

public:
    static std::map<std::string, timing_session> all_timings;
    static std::vector<std::string> stacked_names;
    static int depth;

public:
    explicit scoped_timer(const std::string& name)
        : before(std::chrono::high_resolution_clock::now())
    {
        depth++;
        stacked_names.emplace_back(name);
        fullname = join(stacked_names, "/");
    }

    ~scoped_timer()
    {

        const auto after = std::chrono::high_resolution_clock::now();

        using chrono_unit = typename unit_to_chrono_unit<U>::type;
        const auto elapsed = static_cast<unsigned int>(std::chrono::duration_cast<chrono_unit>(after - before).count());

        const std::string unit_str = unit_to_chrono_unit<U>::str;
        all_timings[fullname].timings.emplace_back(elapsed);

        if (!stacked_names.empty()) {
            stacked_names.pop_back();
        } else {
        }
        depth--;
    }

    static void print_timings()
    {
        std::cout << "Timings: "
                  << "(unit=" << unit_to_chrono_unit<U>::str << ")" << std::endl;
        int max_name_length = 0;
        for (auto& [name, session] : all_timings) {
            max_name_length = std::max(max_name_length, static_cast<int>(name.size()));
        }
        int col_length = 20;
        int col_count = 4;
        auto print_line = [&](bool border=true) {
            for (auto i = 0; i < max_name_length; ++i) {
                std::cout << "-";
            }

            std::string col_sep = border ? "+" : "|";
            std::cout << col_sep;

            for (auto i = 0; i < col_count; ++i) {
                for (auto j = 0; j < col_length; ++j) {
                    std::cout << "-";
                }
                if (i < col_count - 1) {
                    std::cout << col_sep;
                }
            }
            std::cout << "|" << std::endl;
        };

        print_line();

        std::cout << std::setw(max_name_length) << "name"
                  << "|" << std::right << std::setw(col_length) << "min"
                  << "|" << std::right << std::setw(col_length) << "max"
                  << "|" << std::right << std::setw(col_length) << "avg"
                  << "|" << std::right << std::setw(col_length) << "sample count"
                  << "|" << std::endl;

        print_line(false);

        for (auto& [name, session] : all_timings) {
            const auto count = session.timings.size();
            const auto avg = std::accumulate(session.timings.cbegin(), session.timings.cend(), 0.f)
                / static_cast<float>(count);
            const auto min = *std::min_element(session.timings.cbegin(), session.timings.cend());
            const auto max = *std::max_element(session.timings.cbegin(), session.timings.cend());
            const auto precision = 5;
            // clang-format off
                std::cout << std::left << std::setw(max_name_length) << name << "|"
                          << std::right << std::setw(col_length) << std::setprecision(precision) << min << "|"
                          << std::right << std::setw(col_length) << std::setprecision(precision) << max << "|"
                          << std::right << std::setw(col_length) << std::setprecision(precision) << avg << "|"
                          << std::right << std::setw(col_length) << session.timings.size() << "|" << std::endl;
                //clang-format on
            }

            print_line();
        }
    };

typedef scoped_timer<unit::ms> scoped_timer_ms;
typedef scoped_timer<unit::us> scoped_timer_us;
typedef scoped_timer<unit::ns> scoped_timer_ns;

}

template<timings::unit U> std::map<std::string, timings::timing_session> timings::scoped_timer<U>::all_timings;
template<timings::unit U> std::vector<std::string> timings::scoped_timer<U>::stacked_names;
template<timings::unit U> int timings::scoped_timer<U>::depth = 0;
