(function () {
  "use strict";
  const SDK = window.__HERMES_PLUGIN_SDK__;
  if (!SDK || !window.__HERMES_PLUGINS__) return;
  const h = SDK.React.createElement;
  function Work() {
    return h("div", {style:{height:"calc(100dvh - 100px)",minHeight:"480px"}},
      h("iframe", {title:"Windance Work", src:"/api/plugins/windance-vega-desktop/work", style:{width:"100%",height:"100%",border:0,borderRadius:"12px"}}));
  }
  window.__HERMES_PLUGINS__.register("windance-vega-desktop", Work);
})();
