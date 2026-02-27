import { cn } from "@/lib/utils";
import { roboto } from "@/lib/font";
import Image from "next/image";
import { Button } from "./ui/button";
import Link from "next/link";

function Navbar() {
  return (
    <div className="w-full flex justify-center fixed z-20 bg-transparent navbar">
      <div
        className={cn(
          "bg-white w-fit p-4 mt-4 rounded-2xl shadow-card flex flex-row gap-4",
        )}
      >
        <Link href={"/"} className="flex justify-center items-center">

          <div className="flex flex-row  gap-4 items-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 32 36"
              fill="none"
              className="w-full h-[28px]"
            >
              <path
                d="M0.218809 6.39372C-0.583387 2.32966 3.81252 -0.760366 7.36492 1.37048L29.0704 14.3901C33.1176 16.8177 31.57 23.019 26.8567 23.2603L20.7437 23.5732C18.9086 23.6671 17.29 24.8049 16.5803 26.4998L14.2161 32.1458C12.3932 36.499 6.03422 35.8556 5.12029 31.2255L0.218809 6.39372Z"
                fill="url(#paint0_linear)"
                fillOpacity="0.8"
              />
              <defs>
                <linearGradient
                  id="paint0_linear"
                  x1="20.9724"
                  y1="28.3233"
                  x2="2.15889"
                  y2="1.55901"
                  gradientUnits="userSpaceOnUse"
                >
                  <stop stopColor="#ED7998" />
                  <stop offset="1" stopColor="#FDC7D6" />
                </linearGradient>
              </defs>
            </svg>
            <p className={cn("font-semibold text-xl", roboto.className)}>
              Memora.dev
            </p>
          </div>
        </Link>
        <div>
          <GhostButton name={"Pricing"} href="/pricing" />
          <GhostButton name={"Customers"} />
          <GhostButton name={"How it Works"} href="/how-it-works" />
          <GhostButton name={"Contact"} />
        </div>
        <Link href={"/login"}>
          <Button className="cursor-pointer" variant={"outline"}>
            Log in
          </Button>
        </Link>
        <Button className="bg-black hover:shadow-xl hover:-translate-y-0.5 hover:bg-black transition-all cursor-pointer">
          Book a demo
        </Button>
      </div>
    </div>
  );
}

const GhostButton = ({ name, href }: { name: string; href?: string }) => {
  const btn = (
    <Button className="text-gray-500 cursor-pointer" variant="ghost">
      {name}
    </Button>
  );

  return href ? <Link href={href}>{btn}</Link> : btn;
};

export default Navbar;
