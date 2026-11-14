// Picks a food emoji and a cover colour from text. Purely decorative (there are no photos in the data).
const CUISINES = [
  [/south indian|dosa|idli/i, "🥞", "sun"],
  [/italian|pizza|pasta/i, "🍕", "tomato"],
  [/chinese|noodle|asian/i, "🍜", "plum"],
  [/snack|beverage|cafe|coffee|tea/i, "☕", "leaf"],
  [/biryani|north indian|mughlai/i, "🍛", "sun"],
  [/dessert|sweet|ice/i, "🍨", "plum"],
];
const DISHES = [
  [/dosa/i, "🥞"], [/idli|vada/i, "🧆"], [/meal|thali/i, "🍛"], [/biryani|rice/i, "🍚"],
  [/noodle/i, "🍜"], [/pizza/i, "🍕"], [/pasta/i, "🍝"], [/burger/i, "🍔"], [/sandwich/i, "🥪"],
  [/fries/i, "🍟"], [/samosa|puff/i, "🥟"], [/coffee|tea|chai/i, "☕"], [/juice|shake|lassi|cola|soda/i, "🥤"],
  [/cake|brownie|dessert|ice/i, "🍰"], [/soup/i, "🍲"], [/paneer/i, "🧀"], [/egg/i, "🍳"], [/chicken/i, "🍗"],
];
const COVERS = ["sun", "tomato", "plum", "leaf"];

export function cuisineLook(cuisine = "", seed = 0) {
  const hit = CUISINES.find(([re]) => re.test(cuisine));
  return hit ? { emoji: hit[1], tone: hit[2] } : { emoji: "🍽️", tone: COVERS[seed % COVERS.length] };
}

export function dishEmoji(name = "", category = "") {
  const hit = DISHES.find(([re]) => re.test(name)) || DISHES.find(([re]) => re.test(category));
  return hit ? hit[1] : "🍽️";
}
