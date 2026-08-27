import axios from 'axios'

const apiClient = axios.create({
  baseURL: 'https://api.openweathermap.org/data/2.5',
  timeout: 10000,
})

const geoClient = axios.create({
  baseURL: 'https://api.openweathermap.org/geo/1.0',
  timeout: 10000,
})

const koreanGeoClient = axios.create({
  baseURL: 'https://geocoding-api.open-meteo.com/v1',
  timeout: 10000,
})

const conditionLabels = {
  Clear: '맑음',
  Clouds: '구름',
  Rain: '비',
  Drizzle: '이슬비',
  Snow: '눈',
  Thunderstorm: '천둥번개',
  Mist: '안개',
}

// API 상태 코드를 자연스러운 화면 안내 문구로 변환한다.
const conditionDescriptions = {
  Clear: '맑고 화창한 날씨예요.',
  Clouds: '구름이 많은 날씨예요.',
  Rain: '비가 내리고 있어요. 우산을 챙기세요.',
  Drizzle: '이슬비가 내리고 있어요.',
  Snow: '눈이 내리고 있어요. 길이 미끄러울 수 있어요.',
  Thunderstorm: '천둥과 번개가 칠 수 있어요. 외출에 주의하세요.',
  Mist: '안개가 껴 있어요. 이동할 때 주의하세요.',
}

const getApiKey = () => {
  const apiKey = import.meta.env.VITE_OPENWEATHER_API_KEY

  if (!apiKey) {
    throw new Error('OpenWeatherMap API 키가 설정되지 않았습니다.')
  }

  return apiKey
}

const initialRomanization = [
  'g',
  'kk',
  'n',
  'd',
  'tt',
  'r',
  'm',
  'b',
  'pp',
  's',
  'ss',
  '',
  'j',
  'jj',
  'ch',
  'k',
  't',
  'p',
  'h',
]
const vowelRomanization = [
  'a',
  'ae',
  'ya',
  'yae',
  'eo',
  'e',
  'yeo',
  'ye',
  'o',
  'wa',
  'wae',
  'oe',
  'yo',
  'u',
  'wo',
  'we',
  'wi',
  'yu',
  'eu',
  'ui',
  'i',
]
const finalRomanization = [
  '',
  'k',
  'k',
  'k',
  'n',
  'n',
  'n',
  't',
  'l',
  'k',
  'm',
  'p',
  'l',
  'l',
  'l',
  'p',
  'l',
  'm',
  'p',
  'p',
  't',
  't',
  'ng',
  't',
  't',
  'k',
  't',
  'p',
  't',
]

// 한글 검색 결과가 없을 때 사용할 간단한 로마자 변환
const romanizeKorean = (text) => {
  return [...text]
    .map((character) => {
      const code = character.charCodeAt(0) - 0xac00

      if (code < 0 || code > 11171) {
        return character
      }

      const initial = Math.floor(code / 588)
      const vowel = Math.floor((code % 588) / 28)
      const final = code % 28

      return `${initialRomanization[initial]}${vowelRomanization[vowel]}${finalRomanization[final]}`
    })
    .join('')
}

// 도시명을 좌표로 통일한 뒤 현재 날씨와 예보 API에서 공통으로 사용한다.
const getCoordinates = async (city, apiKey) => {
  const response = await geoClient.get('/direct', {
    params: {
      q: city,
      limit: 1,
      appid: apiKey,
    },
  })

  const location = response.data[0]

  if (location) {
    return location
  }

  // OpenWeatherMap에 없는 국내 지명은 Open-Meteo 지오코딩으로 보완한다.
  const koreanCityQuery = city.endsWith('시') ? city : `${city}시`
  const koreanResponse = await koreanGeoClient.get('/search', {
    params: {
      name: koreanCityQuery,
      count: 5,
      language: 'ko',
      format: 'json',
    },
  })
  const koreanLocation = koreanResponse.data.results?.find((item) => item.country_code === 'KR')

  if (koreanLocation) {
    return {
      lat: koreanLocation.latitude,
      lon: koreanLocation.longitude,
    }
  }

  const romanizedCity = romanizeKorean(city)
  const romanizedResponse = await geoClient.get('/direct', {
    params: {
      q: romanizedCity,
      limit: 1,
      appid: apiKey,
    },
  })
  const romanizedLocation = romanizedResponse.data[0]

  if (!romanizedLocation) {
    throw new Error('입력한 도시를 찾지 못했습니다.')
  }

  return romanizedLocation
}

export const getCurrentWeather = async (city) => {
  const apiKey = getApiKey()
  const location = await getCoordinates(city, apiKey)

  const response = await apiClient.get('/weather', {
    params: {
      lat: location.lat,
      lon: location.lon,
      appid: apiKey,
      units: 'metric',
      lang: 'kr',
    },
  })

  const data = response.data
  const rawCondition = data.weather[0].main

  return {
    id: `api-${data.id}`,
    city,
    condition: conditionLabels[rawCondition] || data.weather[0].description,
    temperature: Math.round(data.main.temp),
    feelsLike: Math.round(data.main.feels_like),
    humidity: data.main.humidity,
    windSpeed: data.wind.speed,
    pressure: data.main.pressure,
    description: conditionDescriptions[rawCondition] || '현재 날씨 정보를 확인해 보세요.',
  }
}

export const getFiveDayForecast = async (city) => {
  const apiKey = getApiKey()
  const location = await getCoordinates(city, apiKey)

  const response = await apiClient.get('/forecast', {
    params: {
      lat: location.lat,
      lon: location.lon,
      appid: apiKey,
      units: 'metric',
      lang: 'kr',
    },
  })

  return response.data.list
    .filter((item) => item.dt_txt.includes('12:00:00'))
    .slice(0, 5)
    .map((item) => {
      const rawCondition = item.weather[0].main

      return {
        date: new Intl.DateTimeFormat('ko-KR', {
          weekday: 'short',
          month: 'numeric',
          day: 'numeric',
        }).format(new Date(item.dt * 1000)),
        condition: conditionLabels[rawCondition] || item.weather[0].description,
        temperature: Math.round(item.main.temp),
      }
    })
}
