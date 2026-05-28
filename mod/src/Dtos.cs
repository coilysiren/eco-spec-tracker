using System.Text.Json.Serialization;
using Newtonsoft.Json;

namespace EcoJobsTracker;

// Dual JSON attributes so DTOs serialize camelCase under System.Text.Json
// (shell harness) or Newtonsoft.Json (Eco's web pipeline). See docs/FEATURES.md.
public record SpecialtyDto(
    [property: JsonPropertyName("name"), JsonProperty("name")] string Name,
    [property: JsonPropertyName("level"), JsonProperty("level")] int Level,
    [property: JsonPropertyName("maxLevel"), JsonProperty("maxLevel")] int MaxLevel);

// lastSeen is an ISO-8601 UTC timestamp or null (never logged in). The Python
// tracker derives "active" from this vs now(), so the mod stays window-agnostic.
public record PlayerSkillsDto(
    [property: JsonPropertyName("player"), JsonProperty("player")] string Player,
    [property: JsonPropertyName("lastSeen"), JsonProperty("lastSeen")] string? LastSeen,
    [property: JsonPropertyName("specialties"), JsonProperty("specialties")] SpecialtyDto[] Specialties);
