import React from "react";
import PremiumChat from "./components/PremiumChat";

export default function App(){
  return (
    <div style={{ minHeight: "100vh", fontFamily: "Inter, system-ui, Arial" }}>
      {/* your page content can be here */}
      <div style={{ padding: 36, color: "#fff" }}>
        <h1>Product / Landing page (demo)</h1>
        <p style={{ maxWidth: 680 }}>
          This page shows the PremiumChat floating widget (bottom-right). Open it to begin chatting.
        </p>
      </div>

      <PremiumChat />
    </div>
  );
}
