"""
Database Schemas for RPG Admin

Each Pydantic model represents a collection in your database.
Collection name is the lowercase of the class name.

This schema set is designed for an RPG Discord bot backoffice to manage:
- Items (gear, sets, consumables, etc.)
- Loot Tables (per chest or source)
- Expeditions (configurable rewards and stat checks)
- Titles (cosmetic unlocks)
- Backgrounds (profile cosmetics)
- Activity Rewards (per activity configuration)
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

# -----------------------------
# Core Shared Sub-models
# -----------------------------

class StatBlock(BaseModel):
    """Generic stat block for items/sets/expeditions checks."""
    strength: int = 0
    agility: int = 0
    intelligence: int = 0
    vitality: int = 0
    luck: int = 0
    defense: int = 0
    power: int = 0

class RecipeIngredient(BaseModel):
    item_id: str = Field(..., description="ID of required ingredient item")
    quantity: int = Field(1, ge=1)

class Recipe(BaseModel):
    ingredients: List[RecipeIngredient] = Field(default_factory=list)
    crafting_time_sec: int = Field(0, ge=0)
    crafting_cost: int = Field(0, ge=0, description="Gold or currency cost")

class ImageData(BaseModel):
    url: Optional[str] = Field(None, description="Direct image URL")
    alt: Optional[str] = None

# -----------------------------
# Collections
# -----------------------------

class Item(BaseModel):
    """Items used across the game: gear, sets, consumables, materials."""
    name: str
    description: Optional[str] = None
    item_type: Literal[
        "weapon", "armor", "accessory", "set", "consumable", "material", "key", "misc"
    ] = "misc"
    rarity: Literal["common", "uncommon", "rare", "epic", "legendary", "mythic"] = "common"
    price: int = Field(0, ge=0)
    image: Optional[ImageData] = None
    stats: StatBlock = Field(default_factory=StatBlock)
    set_parts: List[str] = Field(default_factory=list, description="If part of a set, IDs of related items")
    recipe: Optional[Recipe] = None
    tradable: bool = True
    stack_size: int = Field(1, ge=1)
    tags: List[str] = Field(default_factory=list)

class LootEntry(BaseModel):
    item_id: str
    drop_rate: float = Field(..., ge=0.0, le=1.0, description="Probability 0-1")
    quantity_min: int = Field(1, ge=1)
    quantity_max: int = Field(1, ge=1)

class LootTable(BaseModel):
    """Loot configuration for a chest or source."""
    name: str
    chest_type: Literal["wood", "iron", "gold", "diamond", "event", "boss", "custom"] = "custom"
    entries: List[LootEntry] = Field(default_factory=list)
    rolls: int = Field(1, ge=1, description="How many entries are rolled per open")

class Reward(BaseModel):
    gold: int = 0
    exp: int = 0
    items: List[LootEntry] = Field(default_factory=list)

class StatCheck(BaseModel):
    stat: Literal["strength", "agility", "intelligence", "vitality", "luck", "defense", "power"]
    threshold: int = Field(..., ge=0)
    success_modifier: float = Field(1.0, ge=0.0, description="Multiplier for rewards on success")
    fail_penalty: float = Field(1.0, ge=0.0, description="Multiplier for rewards on failure")

class Expedition(BaseModel):
    name: str
    description: Optional[str] = None
    duration_minutes: int = Field(30, ge=1)
    base_rewards: Reward = Field(default_factory=Reward)
    loot_table_id: Optional[str] = Field(None, description="Reference to a LootTable")
    loot_rolls: int = Field(1, ge=0)
    stat_checks: List[StatCheck] = Field(default_factory=list)
    recommended_stats: StatBlock = Field(default_factory=StatBlock)
    required_level: int = Field(1, ge=1)

class Title(BaseModel):
    name: str
    description: Optional[str] = None
    rarity: Literal["common", "uncommon", "rare", "epic", "legendary", "mythic"] = "common"
    acquisition: Optional[str] = Field(None, description="How it is unlocked")

class Background(BaseModel):
    name: str
    description: Optional[str] = None
    image: Optional[ImageData] = None
    rarity: Literal["common", "uncommon", "rare", "epic", "legendary", "mythic"] = "common"

class ActivityReward(BaseModel):
    """Per-activity configuration for rewards and chances."""
    activity_key: str = Field(..., description="Unique key e.g. fishing, mining, questing")
    base_rewards: Reward = Field(default_factory=Reward)
    loot_table_id: Optional[str] = None
    loot_rolls: int = Field(0, ge=0)
    modifiers: Dict[str, float] = Field(default_factory=dict, description="Any multipliers by condition")

# -----------------------------
# Registry helper for FastAPI
# -----------------------------

MODEL_REGISTRY: Dict[str, Any] = {
    "item": Item,
    "loottable": LootTable,
    "expedition": Expedition,
    "title": Title,
    "background": Background,
    "activityreward": ActivityReward,
}


def get_model_by_collection(collection: str):
    return MODEL_REGISTRY.get(collection.lower())


def schema_summary() -> Dict[str, Any]:
    """Return JSON schema and field summaries for each model to power generic UIs."""
    out: Dict[str, Any] = {}
    for name, model in MODEL_REGISTRY.items():
        out[name] = {
            "title": model.__name__,
            "collection": name,
            "schema": model.model_json_schema(),
        }
    return out
