import { createApp } from "vue";
import App from "./App.vue";
import "./style.css";

const app = createApp(App);

app.config.errorHandler = (err, instance, info) => {
  console.error("[Vue Error]", err, info);
};

app.config.warnHandler = (msg, instance, trace) => {
  if (msg.includes("Failed to resolve component")) return;
  console.warn("[Vue Warn]", msg, trace);
};

app.mount("#app");
