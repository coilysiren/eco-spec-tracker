using Eco.Gameplay.Players;
using Eco.Shared.Time;
using Microsoft.AspNetCore.Mvc;

namespace EcoJobsTracker;

// Lives inside the Eco server process. Eco's ASP.NET Core host picks up
// [ApiController] classes from mod assemblies via AddApplicationPart.
[ApiController]
[Route("api/v1/skills")]
public class SkillsApiController : ControllerBase
{
    [HttpGet]
    public IEnumerable<PlayerSkillsDto> Get()
    {
        var nowUtc = DateTime.UtcNow;
        var nowGameSeconds = TimeUtil.Seconds;

        return UserManager.Users.Select(user =>
        {
            var specialties = user.Skillset.Skills
                .Where(skill => skill.Level > 0 && skill.IsSpecialty)
                .Select(skill => new SpecialtyDto(
                    skill.DisplayName,
                    skill.Level,
                    skill.MaxLevel))
                .ToArray();

            // user.LogoutTime is Eco WorldTime seconds. Anchor to wall-clock as
            // nowUtc minus elapsed game-seconds. The active-in-N-days bucket absorbs it.
            string? lastSeen = null;
            if (user.LoggedIn)
            {
                lastSeen = nowUtc.ToString("yyyy-MM-ddTHH:mm:ssZ");
            }
            else if (user.LogoutTime > 0)
            {
                var ago = TimeSpan.FromSeconds(nowGameSeconds - user.LogoutTime);
                lastSeen = (nowUtc - ago).ToString("yyyy-MM-ddTHH:mm:ssZ");
            }

            return new PlayerSkillsDto(user.Name, lastSeen, specialties);
        });
    }
}
