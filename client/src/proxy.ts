import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  const token = request.cookies.get("access_token_cookie");
  const pathname = request.nextUrl.pathname;

  console.log(`[Middleware] 📍 ${pathname} | cookie present: ${!!token}`);

  // NOTE: If your backend is on a different domain (e.g. CloudFront vs Amplify),
  // the cookie will NOT be visible here due to browser SameSite/cross-site rules.
  // Auth guard is handled client-side by AuthContext instead.
  // We allow all dashboard routes through and let the client handle redirects.

  if (!token && pathname.startsWith("/dashboard")) {
    console.log(`[Middleware] ⚠️ No cookie found for ${pathname}. ` +
      `If backend is on a different domain, this is expected \u2014 client-side auth will handle it.`);
    // Do NOT redirect here \u2014 the client-side AuthContext will handle unauthorized access
    // return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};