"use client";
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
import { useState } from "react";
import { register } from "@/services/auth";
import { toast } from "sonner";

export default function RegisterPage() {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const handleSubmit = async (e: React.SubmitEvent) => {
    e.preventDefault();
    setLoading(true);
    if (formData.password != formData.confirmPassword) {
      toast("Both Password must match");
      return;
    }
    try {
      const res = await register(
        formData.email,
        formData.password,
        formData.name,
      );
      const message = res.data.message;
      toast(message);
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { message?: string } } }).response?.data?.message || "Something went wrong. Try again.";
      toast(message);
    } finally {
      setLoading(false);
    }
  };
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.id]: e.target.value,
    });
  };
  return (
    <div className="min-h-screen flex items-center justify-center p-4 pt-30">
      <Card className="w-full max-w-md rounded-2xl z-10">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">
            Create an account
          </CardTitle>
          <CardDescription className="text-center">
            Enter your details to get started
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleSubmit} className="space-y-2">
            <div className="">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                onChange={handleChange}
                type="text"
                placeholder="John Doe"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="name@example.com"
                required
                onChange={handleChange}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Create a password"
                required
                onChange={handleChange}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="Confirm your password"
                required
                onChange={handleChange}
              />
            </div>
            <Button
              className="w-full bg-black hover:bg-black/80 cursor-pointer"
              type="submit"
              disabled={loading}
            >
             {loading ? 'Please wait...' :  'Create account' }
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
          </form>

          <Button
            variant="outline"
            className="w-full cursor-pointer"
            type="button"
            disabled={loading}
            onClick={() =>
              (window.location.href = "http://memora-alb-902286918.us-west-2.elb.amazonaws.com/auth/github")
            }
          >
            <Image
              src="/github.svg"
              alt="GitHub"
              width={20}
              height={20}
              className="mr-2"
              
            />
            Sign up with GitHub
          </Button>

          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <a
              href="/login"
              className="text-primary hover:underline font-medium"
            >
              Login
            </a>
          </p>
        </CardContent>
      </Card>
      <div className=" fixed -bottom-12 left-0 right-0 opacity-15 flex flex-row">
        <Image src="/bara.svg" alt="bara" width={300} height={200} />
        <Image src="/tm.svg" alt="bara" width={300} height={200} />
        <Image src="/goi.svg" alt="bara" width={300} height={200} />
        <Image src="/junction.svg" alt="bara" width={300} height={200} />
      </div>
    </div>
  );
}
