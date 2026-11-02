(function () {
  try {
    var theme = localStorage.getItem("syllanix-theme");
    if (theme !== "warm" && theme !== "light" && theme !== "dark") { theme = "warm"; }
    document.documentElement.setAttribute("data-theme", theme);
  } catch (error) {
    document.documentElement.setAttribute("data-theme", "warm");
  }
})();