export const metadata = { title: "The System — Awakening" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ background: "#090D13", color: "#F3F7FB", fontFamily: "system-ui, sans-serif", margin: 0, padding: 0 }}>
        {children}
      </body>
    </html>
  );
}
