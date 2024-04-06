#include <fpm/fixed.hpp>
#define STB_IMAGE_IMPLEMENTATION
#include <stb_image.h>
#include <iostream>
#include <vector>
#include <fstream>
#include <scoped_timer.hpp>


using fixed_q8_4 = fpm::fixed<std::uint8_t, std::uint16_t, 4>;
using fixed_q16_4 = fpm::fixed<std::uint16_t, std::uint32_t, 6>;

template<typename T>
struct image
{
    image(size_t w, size_t h) :width(w), height(h), pixels(h* w) {}
    const T& at(size_t i, size_t j) const { return pixels[width * i + j]; }
    void set(size_t i, size_t j, const T& val) { pixels[width * i + j] = val; }
    size_t count() const { return width * height; }
    size_t width, height;
    std::vector<T> pixels;
};


template<typename T>
void imwrite(const image<T>&im, std::string filepath)
{
    std::ofstream of(filepath, std::ios::binary);
    //of << static_cast<uint16_t>(im.width) << static_cast<uint16_t>(im.height);
    of.write(reinterpret_cast<const char*>(&im.pixels[0]), im.count()*sizeof(T));
    of.close();
}

template<typename T>
void vecwrite(const std::vector<T>&vec, std::string filepath)
{
    std::ofstream of(filepath, std::ios::binary);
    of.write(reinterpret_cast<const char*>(&vec[0]), vec.size() * sizeof(T));
    of.close();

}

template<typename T>
void binning_2x2_fxp(image<T>& im, image<T>&out)
{
    const auto w = out.width;
    const auto h = out.height;
    for(auto i=0u; i<h; ++i)
    {
        for (auto j = 0u; j < w; ++j)
        {
            const auto p00 = im.at(i * 2, j * 2);
            const auto p01 = im.at(i * 2, j * 2+1);
            const auto p10 = im.at(i * 2+1, j * 2);
            const auto p11 = im.at(i * 2+1, j * 2+1);
            T p_b = p00 + p01 + p10 + p11;
            p_b = p_b / 4;
            out.set(i, j, p_b);
        }
    }


}

const int trycount = 400;


template<typename T>
image<T>load_image_fxp(const char* filename)
{
    int w, h, ch;
    stbi_uc* pixels = stbi_load(filename, &w, &h, &ch, 1);

    image<T> im(w, h);
    for(int i=0; i<w*h; ++i)
    {
        im.pixels[i] = T(pixels[i]);
    }
    return im;
}

int main(int argc, char* argv[])
{
    std::string filepath;
    if(argc == 1)
    {
        filepath = "camera.png";
    }
    else
    {
        filepath = argv[1];
    }


    image<uint8_t> im_u8 = load_image_fxp<uint8_t>(filepath.c_str());
    const size_t w = im_u8.width, h = im_u8.height;
    image<uint8_t> out_u8(w / 2, h / 2);



    image<float> im_f32(w, h);
    image<float> out_f32(w/2, h/2);
    for(size_t i=0; i < im_u8.count(); ++i)
    {
        im_f32.pixels[i] = static_cast<float>(im_u8.pixels[i]) / 255.0f;
    }

    image<fixed_q8_4> im_q8_4 = load_image_fxp<fixed_q8_4>("camera.png");
    image<fixed_q8_4> out_q8_4(w/2, h/2);

    image<fixed_q16_4> im_q16_4 = load_image_fxp<fixed_q16_4>("camera.png");
    image<fixed_q16_4> out_q16_4(w / 2, h / 2);

    for (auto r = 0; r < trycount; ++r)
    {
        timings::scoped_timer_us timer("binnin2x2_q8_4");
        binning_2x2_fxp(im_q8_4, out_q8_4);
    }

    for (auto r = 0; r < trycount; ++r)
    {
        timings::scoped_timer_us timer("binnin2x2_q16_4");
        binning_2x2_fxp(im_q16_4, out_q16_4);
    }

    for (auto r = 0; r < trycount; ++r)
    {
        timings::scoped_timer_us timer("binnin2x2_u8");
        binning_2x2_fxp(im_u8, out_u8);
    }

    for (auto r = 0; r < trycount; ++r)
    {
        timings::scoped_timer_us timer("binnin2x2_f32");
        binning_2x2_fxp(im_f32, out_f32);
    }

    timings::scoped_timer_us::print_timings();

    std::vector<float> out_q8_4_f32(out_q8_4.pixels.begin(), out_q8_4.pixels.end());
    std::vector<float> out_q16_4_f32(out_q16_4.pixels.begin(), out_q16_4.pixels.end());

    imwrite(out_u8, "out_u8.bin");
    vecwrite(out_q8_4_f32, "out_q8_4_f32.bin");
    vecwrite(out_q16_4_f32, "out_q16_4_f32.bin");
    imwrite(out_q8_4, "out_q8_4.bin");
    imwrite(out_f32, "out_f32.bin");
    
    //std::cout << a << std::endl;

    return 0;
}