import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import Image from "next/image";

export default function LoginPage() {
  return (
    <div className="max-h-screen min-h-screen overflow-hidden relative flex items-center justify-center  p-4">
      <Card className="w-full max-w-md rounded-2xl z-10">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">
            Welcome back
          </CardTitle>
          <CardDescription className="text-center">
            Enter your credentials to login
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="name@example.com"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Enter your password"
              required
            />
          </div>
          <Button
            className="w-full bg-black hover:bg-black/80 cursor-pointer"
            type="submit"
          >
            Sign in
          </Button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">
                Or continue using
              </span>
            </div>
          </div>

          <Button
            variant="outline"
            className="w-full cursor-pointer"
            type="button"
          >
            <Image
              src="/github.svg"
              alt="GitHub"
              width={20}
              height={20}
              className="mr-2"
            />
            Login using GitHub
          </Button>

          <p className="text-center text-sm text-muted-foreground">
            Don&apos;t have an account?{" "}
            <a
              href="/register"
              className="text-primary hover:underline font-medium"
            >
              Register
            </a>
          </p>
        </CardContent>
      </Card>
      <div className="absolute -bottom-12 left-0 right-0 opacity-15 flex flex-row">
        <Image src="/bara.svg" alt="bara" width={300} height={200} />
        <Image src="/tm.svg" alt="bara" width={300} height={200} />
        <Image src="/goi.svg" alt="bara" width={300} height={200} />
        <Image src="/junction.svg" alt="bara" width={300} height={200} />
      </div>
    </div>
  );
}
