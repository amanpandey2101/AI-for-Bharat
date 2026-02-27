import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import "./home.css";
import { AppSidebar } from "@/components/app-sidebar";
import { AuthProvider } from "@/context/AuthContext";
function page({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <AuthProvider>

    <SidebarProvider>
      <AppSidebar />
      <main>
        <SidebarTrigger />
        {children}
      </main>
    </SidebarProvider>
    </AuthProvider>
  );
}

export default page;
