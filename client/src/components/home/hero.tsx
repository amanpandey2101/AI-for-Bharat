import { cn } from "@/lib/utils";
import React from "react";
import { Button } from "../ui/button";
import { TextAnimate } from "../ui/text-animate";
import Image from "next/image";

function Hero() {
  return (
    <div className="w-full relative flex h-[60vh] justify-center items-center flex-col gap-4">
      <div className="absolute   right-[17%]">
        <Image
          alt="pink-cap"
          width={200}
          height={200}
          className=" right-beanie rotate-180 float"
          loading="eager"
          src={
            "https://cdn.prod.website-files.com/62b5b85dd560583e288cb389/684bb6c01209fda7efc5ae91_pink-cap-poster-min.png"
          }
        />
      </div>
      <div className="absolute right-[7%]  mb-32">
        <Image
          alt="green-beanie"
          width={150}
          height={150}
          loading="eager"
          className=" right-beanie float rotate-180"
          src={
            "https://cdn.prod.website-files.com/62b5b85dd560583e288cb389/684bb6c0603d001f907c07fe_green-beanie-min.png"
          }
        />
      </div>
      <div className="absolute left-[17%] mb-32">
        <Image
        alt="blue-beanie"
        width={150}
        height={150}
        loading={"eager"}
        src={"https://cdn.prod.website-files.com/62b5b85dd560583e288cb389/684bb42305d94da4db545cfd_09e7c970fd10f7c999bd7537573f5820_blue-cap-poster-min.png"}
        />
      </div>
      <h2 className={cn("text-center text-6xl font-semibold")}>
        <TextAnimate animation="blurIn" by="word">
          We are the archives
        </TextAnimate>
      </h2>
      <h2 className="text-md text-gray-500">
        <TextAnimate animation="slideUp" by="word">
          Organize your history. Create impactful teams. Stop the memory loss.
        </TextAnimate>
      </h2>
      <div className="gap-4 flex flex-row">
        <Button className="h-12 cursor-pointer shadow-card" variant={"outline"}>
          Watch Video
        </Button>
        <Button className="bg-black  hover:shadow-xl h-12 hover:-translate-y-0.5 hover:bg-black transition-all cursor-pointer">
          Book a demo
        </Button>
      </div>
    </div>
  );
}

export default Hero;
