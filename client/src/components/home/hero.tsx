import { cn } from "@/lib/utils";
import React from "react";
import { Button } from "../ui/button";
import { TextAnimate } from "../ui/text-animate";
import Image from "next/image";
import Link from "next/link";

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
          className={cn("text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold tracking-tighter leading-[0.9] text-black mb-6")}
        >
          We are archives
        </TextAnimate>

        <TextAnimate
          as="p"
          animation="slideUp"
          by="word"
          className="text-lg md:text-xl text-gray-500 max-w-[90%] md:max-w-2xl font-medium tracking-tight leading-relaxed"
        >
          Capture every architectural &quot;Why&quot; where it happens. Stop losing context in Slack threads. Onboard developers in seconds with Memora&apos;s AI-driven knowledge graph.
        </TextAnimate>

        <div className="gap-4 flex flex-col sm:flex-row mt-12 w-full sm:w-auto px-10 sm:px-0">
          <Button className="h-16 px-10 text-lg font-semibold w-full sm:w-auto cursor-pointer shadow-sm rounded-2xl hover:bg-gray-50 transition-all" variant={"outline"}>
             See the Demo
          </Button>
          <Link href="/login" className="w-full sm:w-auto">
            <Button className="bg-violet-600 text-white hover:shadow-violet-200 hover:shadow-2xl h-16 px-10 text-lg font-semibold w-full hover:-translate-y-1 hover:bg-violet-700 transition-all duration-300 cursor-pointer rounded-2xl">
              Get Started Free
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default Hero;
