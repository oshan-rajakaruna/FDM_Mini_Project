import { WEATHER_STATIONS, WIND_DIRECTIONS } from '../data/weatherOptions.js'

const DAY_IN_MILLISECONDS = 24 * 60 * 60 * 1000
const DATE_RANGE_START = Date.UTC(2007, 10, 1)
const DATE_RANGE_END = Date.UTC(2017, 5, 25)

const SCENARIO_PROFILES = [
  {
    name: 'dry-clear',
    weight: 0.43,
    temperatureGap: [9, 17],
    humidity9am: [35, 70],
    humidity3pm: [20, 55],
    cloud: [0, 3],
    sunshine: [8, 14],
    evaporation: [4, 15],
    gust: [15, 58],
    pressure: [1008, 1035],
  },
  {
    name: 'cloudy',
    weight: 0.27,
    temperatureGap: [7, 14],
    humidity9am: [50, 82],
    humidity3pm: [38, 72],
    cloud: [4, 7],
    sunshine: [2, 8],
    evaporation: [1.5, 9],
    gust: [20, 65],
    pressure: [998, 1026],
  },
  {
    name: 'rainy',
    weight: 0.22,
    temperatureGap: [5, 11],
    humidity9am: [72, 100],
    humidity3pm: [58, 94],
    cloud: [5, 8],
    sunshine: [0, 4.5],
    evaporation: [0, 5],
    gust: [25, 72],
    pressure: [990, 1018],
  },
  {
    name: 'windy-stormy',
    weight: 0.08,
    temperatureGap: [5, 12],
    humidity9am: [68, 98],
    humidity3pm: [55, 92],
    cloud: [6, 8],
    sunshine: [0, 3.5],
    evaporation: [0, 5],
    gust: [55, 90],
    pressure: [985, 1008],
  },
]

function boundedRandom(random) {
  const value = Number(random())
  if (!Number.isFinite(value)) return 0.5
  return Math.min(1 - Number.EPSILON, Math.max(0, value))
}

function randomBetween(random, min, max) {
  return min + boundedRandom(random) * (max - min)
}

function randomInteger(random, min, max) {
  return Math.floor(randomBetween(random, min, max + 1))
}

function roundToOneDecimal(value) {
  return Math.round(value * 10) / 10
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

function choose(random, values) {
  return values[randomInteger(random, 0, values.length - 1)]
}

function chooseProfile(random) {
  const selection = boundedRandom(random)
  let cumulativeWeight = 0

  for (const profile of SCENARIO_PROFILES) {
    cumulativeWeight += profile.weight
    if (selection < cumulativeWeight) return profile
  }

  return SCENARIO_PROFILES[SCENARIO_PROFILES.length - 1]
}

function generateRainfall(random, scenario) {
  if (scenario === 'dry-clear') {
    return boundedRandom(random) < 0.58
      ? 0
      : roundToOneDecimal(randomBetween(random, 0.1, 1) ** 1.2)
  }
  if (scenario === 'cloudy') {
    return boundedRandom(random) < 0.68
      ? roundToOneDecimal(randomBetween(random, 0, 1))
      : roundToOneDecimal(1.1 + (boundedRandom(random) ** 2) * 6.9)
  }
  if (scenario === 'rainy') {
    return roundToOneDecimal(1.1 + (boundedRandom(random) ** 2) * 28.9)
  }
  return roundToOneDecimal(5 + (boundedRandom(random) ** 1.7) * 45)
}

function generateDate(random) {
  const dayCount = Math.floor(
    (DATE_RANGE_END - DATE_RANGE_START) / DAY_IN_MILLISECONDS,
  )
  const timestamp = DATE_RANGE_START
    + randomInteger(random, 0, dayCount) * DAY_IN_MILLISECONDS
  return new Date(timestamp).toISOString().slice(0, 10)
}

function nearbyWindDirection(random, baseIndex, maximumOffset) {
  const offset = randomInteger(random, -maximumOffset, maximumOffset)
  const index = (baseIndex + offset + WIND_DIRECTIONS.length) % WIND_DIRECTIONS.length
  return WIND_DIRECTIONS[index]
}

/**
 * Generate one complete, coherent example observation for the prediction form.
 * The optional random source keeps the generator deterministic in validation.
 */
export function generateRandomWeatherExample(random = Math.random) {
  const profile = chooseProfile(random)
  const minTemp = roundToOneDecimal(randomBetween(random, -5, 30))
  const temperatureGap = randomBetween(random, ...profile.temperatureGap)
  const maxTemp = roundToOneDecimal(clamp(minTemp + temperatureGap, 8, 45))
  const effectiveGap = maxTemp - minTemp
  const temp9am = roundToOneDecimal(
    minTemp + effectiveGap * randomBetween(random, 0.25, 0.52),
  )
  const temp3pm = roundToOneDecimal(
    minTemp + effectiveGap * randomBetween(random, 0.68, 0.97),
  )

  const rainfall = generateRainfall(random, profile.name)
  const baseCloud = randomInteger(random, ...profile.cloud)
  const cloud9am = clamp(baseCloud + randomInteger(random, -1, 1), 0, 8)
  const cloud3pm = clamp(baseCloud + randomInteger(random, -1, 1), 0, 8)
  const pressure9am = roundToOneDecimal(randomBetween(random, ...profile.pressure))
  const pressure3pm = roundToOneDecimal(
    clamp(pressure9am + randomBetween(random, -4, 4), 985, 1035),
  )

  const gustDirectionIndex = randomInteger(random, 0, WIND_DIRECTIONS.length - 1)
  const windGustSpeed = randomInteger(random, ...profile.gust)
  const morningWindMaximum = Math.min(50, Math.floor(windGustSpeed * 0.65))
  const afternoonWindMaximum = Math.min(50, Math.floor(windGustSpeed * 0.75))

  const humidity9am = randomInteger(random, ...profile.humidity9am)
  const humidity3pm = randomInteger(
    random,
    profile.humidity3pm[0],
    Math.min(profile.humidity3pm[1], humidity9am + 5),
  )

  return {
    Date: generateDate(random),
    Location: choose(random, WEATHER_STATIONS),
    RainToday: rainfall > 1 ? 'Yes' : 'No',
    MinTemp: minTemp,
    MaxTemp: maxTemp,
    Temp9am: temp9am,
    Temp3pm: temp3pm,
    Rainfall: rainfall,
    Evaporation: roundToOneDecimal(randomBetween(random, ...profile.evaporation)),
    Sunshine: roundToOneDecimal(randomBetween(random, ...profile.sunshine)),
    WindGustDir: WIND_DIRECTIONS[gustDirectionIndex],
    WindGustSpeed: windGustSpeed,
    WindDir9am: nearbyWindDirection(random, gustDirectionIndex, 2),
    WindDir3pm: nearbyWindDirection(random, gustDirectionIndex, 2),
    WindSpeed9am: randomInteger(random, 0, morningWindMaximum),
    WindSpeed3pm: randomInteger(random, 0, afternoonWindMaximum),
    Humidity9am: humidity9am,
    Humidity3pm: humidity3pm,
    Pressure9am: pressure9am,
    Pressure3pm: pressure3pm,
    Cloud9am: cloud9am,
    Cloud3pm: cloud3pm,
  }
}
