import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const model = {
  services: [],
  connections: {},
  loading: false,
  error: null,

  async init() {
    await this.loadServices();
    await this.loadConnections();
  },

  async loadServices() {
    this.loading = true;
    try {
      const res = await callJsonApi("/mcp_services", { action: "list" });
      this.services = res.data || [];
    } catch (e) {
      this.error = e.message;
    }
    this.loading = false;
  },

  async loadConnections() {
    try {
      const res = await callJsonApi("/mcp_connections", { action: "list" });
      const conns = {};
      for (const c of res.data || []) {
        conns[c.service_id] = c;
      }
      this.connections = conns;
    } catch {
      // Auth not configured — skip
    }
  },

  isConnected(serviceId) {
    return !!this.connections[serviceId];
  },

  getConnection(serviceId) {
    return this.connections[serviceId] || null;
  },

  async connect(serviceId) {
    try {
      const res = await callJsonApi("/mcp_oauth_start", { service_id: serviceId });
      if (res.ok && res.data) {
        const data = res.data;
        if (data.server_url) {
          const popup = window.open(
            "",
            "mcp_oauth",
            "width=600,height=700,scrollbars=yes"
          );
          if (popup) {
            // Listen for OAuth completion message from popup
            const handler = (event) => {
              if (event.data?.type === "mcp_oauth_complete") {
                window.removeEventListener("message", handler);
                this.loadConnections();
              }
            };
            window.addEventListener("message", handler);

            // Set popup content using DOM methods
            const doc = popup.document;
            doc.open();
            const body = doc.body;
            body.style.cssText =
              "font-family:sans-serif;text-align:center;padding:2rem;background:#1a1a1a;color:#eee";
            const h3 = doc.createElement("h3");
            h3.textContent = "Connecting...";
            const p = doc.createElement("p");
            p.textContent = "Redirecting to service authorization...";
            body.appendChild(h3);
            body.appendChild(p);
            doc.close();
          }
        }
      }
    } catch (e) {
      this.error = e.message;
    }
  },

  async disconnect(serviceId) {
    if (!confirm("Disconnect from this service?")) return;
    try {
      await callJsonApi("/mcp_connections", {
        action: "disconnect",
        service_id: serviceId,
      });
      delete this.connections[serviceId];
      // Force reactivity
      this.connections = { ...this.connections };
    } catch (e) {
      this.error = e.message;
    }
  },
};

export const store = createStore("mcpServices", model);
