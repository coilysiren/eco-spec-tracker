using EcoJobsTracker;
using Microsoft.AspNetCore.Mvc;

namespace EcoJobsTracker.Shell;

// Same route as the real mod with canned data, so the Python tracker iterates
// against a live C# server without booting Eco. lastSeen is recomputed per request.
[ApiController]
[Route("api/v1/skills")]
public class MockSkillsController : ControllerBase
{
    private static string Iso(DateTime t) => t.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ");

    [HttpGet]
    public IEnumerable<PlayerSkillsDto> Get()
    {
        var now = DateTime.UtcNow;
        return new[]
        {
            new PlayerSkillsDto("coilysiren", Iso(now), new[]
            {
                new SpecialtyDto("Basic Carpentry", 5, 7),
                new SpecialtyDto("Advanced Carpentry", 3, 7),
                new SpecialtyDto("Furniture Making", 2, 7),
            }),
            new PlayerSkillsDto("ekans", Iso(now.AddHours(-3)), new[]
            {
                new SpecialtyDto("Basic Carpentry", 4, 7),
                new SpecialtyDto("Lumber", 1, 7),
                new SpecialtyDto("Mining", 6, 7),
            }),
            new PlayerSkillsDto("redwood", Iso(now.AddDays(-30)), new[]
            {
                new SpecialtyDto("Glassworking", 5, 7),
                new SpecialtyDto("Basic Masonry", 2, 7),
                new SpecialtyDto("Pottery", 3, 7),
            }),
            new PlayerSkillsDto("salt", Iso(now.AddDays(-2)), new[]
            {
                new SpecialtyDto("Campfire Cooking", 4, 7),
                new SpecialtyDto("Baking", 2, 7),
                new SpecialtyDto("Farming", 5, 7),
                new SpecialtyDto("Gardening", 3, 7),
            }),
            new PlayerSkillsDto("hammerhand", Iso(now.AddDays(-5)), new[]
            {
                new SpecialtyDto("Basic Masonry", 5, 7),
                new SpecialtyDto("Brick Making", 4, 7),
                new SpecialtyDto("Advanced Masonry", 3, 7),
            }),
        };
    }
}
