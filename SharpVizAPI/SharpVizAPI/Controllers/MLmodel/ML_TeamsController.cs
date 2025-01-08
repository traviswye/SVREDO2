using Microsoft.AspNetCore.Mvc;

namespace SharpVizAPI.Controllers.MLmodel
{
    public class ML_TeamsController : Controller
    {
        public IActionResult Index()
        {
            return View();
        }
    }
}
