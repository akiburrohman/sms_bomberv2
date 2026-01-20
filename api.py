# api.py
# এখানে শুধু API add / edit করবে

APIS = [

    {
        "name": "Hisabee",
        "enabled": True,
        "method": "POST",
        "url": "https://app.hishabee.business/api/V2/otp/send",
        "phone_format": "plain",
        "payload": lambda phone: {
            "mobile_number": phone,
            "country_code": "88"
        },
    },

    {
        "name": "Chorki",
        "method": "POST",
        "url": "https://api-dynamic.chorki.com/v2/auth/login?country=BD&platform=web&language=en",
        "phone_format": "plain",   # plain / +88 / 88
        "payload": lambda phone: {"number": phone},
    },

    {
        "name": "Kirei",
        "method": "POST",
        "url": "https://frontendapi.kireibd.com/api/v2/send-login-otp",
        "phone_format": "plain",
        "payload": lambda phone: {"email": phone},
    },

    {
        "name": "DeeptoPlay",
        "method": "POST",
        "url": "https://api.deeptoplay.com/v2/auth/login?country=BD&platform=web&language=en",
        "phone_format": "plain",
        "payload": lambda phone: {"number": phone},
    },

    {
        "name": "PBS",
        "method": "POST",
        "url": "https://apialpha.pbs.com.bd/api/OTP/generateOTP",
        "phone_format": "plain",
        "payload": lambda phone: {"otp": "", "userPhone": phone},
    },

    {
        "name": "BeautyBooth",
        "method": "POST",
        "url": "https://admin.beautybooth.com.bd/api/v2/auth/register",
        "phone_format": "plain",
        "payload": lambda phone: {"token": 91, "type": "phone", "value": phone},
    },

    {
        "name": "Paperfly",
        "method": "POST",
        "url": "https://go-app.paperfly.com.bd/merchant/api/react/registration/request_registration.php",
        "phone_format": "plain",
        "payload": lambda phone: {
            "full_name": "Md RAHIM",
            "company_name": "TestCompany",
            "email_address": "rahim@gmail.com",
            "phone_number": phone
        },
    },

    {
        "name": "Apex4U",
        "method": "POST",
        "url": "https://api.apex4u.com/api/auth/login",
        "phone_format": "plain",
        "payload": lambda phone: {"phoneNumber": phone},
    },

    {
        "name": "Bioscop",
        "method": "POST",
        "url": "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en",
        "phone_format": "plain",
        "payload": lambda phone: {"number": phone},
    },

    {
        "name": "Hoichoi",
        "method": "POST",
        "url": "https://prod-api.hoichoi.dev/core/api/v1/auth/signinup/code",
        "payload": lambda phone: {"phoneNumber": f"+88{phone}"},  # +88 auto add
    },

    {
        "name": "MedEasy",
        "method": "GET",
        "url": lambda phone: f"https://api.medeasy.health/api/send-otp/{phone}/",
        "phone_format": "plain",
        "payload": None,
    },

    {
        "name": "Garibook",
        "method": "POST",
        "url": "https://api.garibookadmin.com/api/v4/user/login",
        "phone_format": "+88",
        "payload": lambda phone: {
            "channel": "web",
            "mobile": phone,
            "recaptcha_token": "garibookcaptcha"
        },
    },

    {
        "name": "Bohubrihi",
        "method": "POST",
        "url": "https://bb-api.bohubrihi.com/public/activity/otp",
        "phone_format": "plain",
        "payload": lambda phone: {
            "intent": "login",
            "phone": phone
        },
    },

    {
        "name": "Bikroy",
        "method": "GET",
        "url": "https://bikroy.com/data/phone_number_login/verifications/phone_login",
        "phone_format": "plain",
        "payload": lambda phone: {"phone": phone},
        "headers": {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }
    },
    
    {
    "name": "RedX",
    "method": "POST",
    "url": "https://api.redx.com.bd/v1/merchant/registration/generate-registration-otp",
    "phone_format": "plain",   # এখানে +88 লাগে না
    "payload": lambda phone: {
        "phoneNumber": phone
        },
    
    },
    
    {
    "name": "Quizgiri",
    "method": "POST",
    "url": "https://developer.quizgiri.xyz/api/v2.0/send-otp",
    "phone_format": "88",   # country_code + phone আলাদা, তাই 88 লাগবে
    "payload": lambda phone: {
        "country_code": "+88",
        "phone": phone.lstrip("0")  # 013 → 13
    },
    
    },
    {
    "name": "Easy",
    "method": "POST",
    "url": "https://core.easy.com.bd/api/v1/registration",
    "payload": lambda phone: {
        "social_login_id": "",
        "name": "Md Rahim",
        "email": "rahim{}@gmail.com".format(phone[-4:]),  # unique email
        "mobile": phone,
        "password": "vvVV::66",
        "password_confirmation": "vvVV::66",
        "device_key": "876f887de09ad8d87b8f8d0932364d5e"
        },
    "headers": {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/json"
        }
    },
    
    {
    "name": "GhooriLearning",
    "method": "POST",
    "url": "https://api.gghoorilearning.com/api/auth/signup/otp?_app_platform=web",
    "payload": lambda phone: {
        "msisdn": phone  # 013XXXXXXXX format
    },
    "headers": {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    },


]
