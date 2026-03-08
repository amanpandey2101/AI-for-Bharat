import { cn } from "@/lib/utils";
import React from "react";
import { Button } from "../ui/button";
import { TextAnimate } from "../ui/text-animate";
import Image from "next/image";

function Hero() {
  return (
    <div className="w-full relative flex min-h-[80vh] md:h-[85vh] justify-center items-center flex-col gap-8 px-4 py-20 md:py-0 overflow-visible">
      
      {/* Container for decorative elements to limit their spread on ultra-wide screens */}
      <div className="absolute inset-0 max-w-[1600px] mx-auto pointer-events-none overflow-visible">
        {/* Pink Cap - Top Right */}
        <div className="absolute right-[2%] md:right-[5%] lg:right-[10%] top-[10%] md:top-[15%] xl:top-[20%] transition-all duration-700 ease-out">
          <Image
            alt="pink-cap"
            width={240}
            height={240}
            className="w-24 md:w-36 lg:w-48 xl:w-56 right-beanie rotate-180 float opacity-40 md:opacity-100"
            loading="eager"
            src={
              "https://cdn.prod.website-files.com/62b5b85dd560583e288cb389/684bb6c01209fda7efc5ae91_pink-cap-poster-min.png"
            }
          />
        </div>

        {/* Green Beanie - Bottom Right */}
        <div className="absolute right-[-2%] md:right-[2%] lg:right-[5%] bottom-[10%] md:bottom-[20%] xl:bottom-[25%] transition-all duration-700 ease-out">
          <Image
            alt="green-beanie"
            width={180}
            height={180}
            loading="eager"
            className="w-20 md:w-28 lg:w-36 xl:w-44 right-beanie float rotate-180 opacity-40 md:opacity-100"
            src={
              "https://cdn.prod.website-files.com/62b5b85dd560583e288cb389/684bb6c0603d001f907c07fe_green-beanie-min.png"
            }
          />
        </div>

        {/* Blue Beanie - Mid Left */}
        <div className="absolute left-[0%] md:left-[3%] lg:left-[8%] top-[15%] md:top-[30%] xl:top-[35%] transition-all duration-700 ease-out">
          <Image
            alt="blue-beanie"
            width={180}
            height={180}
            loading={"eager"}
            className="w-20 md:w-28 lg:w-36 xl:w-44 opacity-40 md:opacity-100 transition-transform duration-300 hover:scale-110"
            src={"https://cdn.prod.website-files.com/62b5b85dd560583e288cb389/684bb42305d94da4db545cfd_09e7c970fd10f7c999bd7537573f5820_blue-cap-poster-min.png"}
          />
        </div>
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center max-w-6xl mx-auto text-center">
        <TextAnimate
          as="h1"
          animation="blurIn"
          by="word"
          className={cn("text-5xl sm:text-6xl md:text-6xl lg:text-7xl xl:text-8xl font-bold tracking-tighter leading-[0.95] md:leading-[1] text-black mb-4")}
        >
          We are the archives
        </TextAnimate>

        <TextAnimate
          as="p"
          animation="slideUp"
          by="word"
          className="text-base md:text-lg text-gray-500 max-w-[85%] md:max-w-xl font-medium tracking-tight"
        >
          Organize your history. Create impactful teams. Stop the memory loss.
        </TextAnimate>

        <div className="gap-4 flex flex-col sm:flex-row mt-10 w-full sm:w-auto px-10 sm:px-0">
          <Button className="h-14 px-8 text-base font-semibold w-full sm:w-auto cursor-pointer shadow-card rounded-full" variant={"outline"}>
            Watch Video
          </Button>
          <Button className="bg-black text-white hover:shadow-2xl h-14 px-8 text-base font-semibold w-full sm:w-auto hover:-translate-y-1 hover:bg-zinc-800 transition-all duration-300 cursor-pointer rounded-full">
            Book a demo
          </Button>
        </div>
      </div>
    </div>
  );
}

export default Hero;
