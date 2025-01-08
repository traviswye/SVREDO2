using SharpVizAPI.Models;
using System.Threading.Tasks;

namespace SharpVizAPI.Services { 
// Interface IClassificationService
public interface IClassificationService
{
    Task<ClassificationResult> ClassificationByPitchingAdvAsync(string date);
    Task<object> ClassificationByAllFactorsAsync(string date);
}

}
