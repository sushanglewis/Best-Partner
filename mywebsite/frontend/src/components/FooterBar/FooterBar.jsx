import React from "react";

export default function FooterBar() {
  return (
    <footer
      style={{
        textAlign: "center",
        padding: "1rem 0",
        fontSize: 14,
        color: "#888",
      }}
    >
      © {new Date().getFullYear()} Shang’s Agent Website. All rights reserved.
    </footer>
  );
}
