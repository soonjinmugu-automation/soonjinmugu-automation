/**
 * 순진무구 자동 문자 발송 시스템
 * Google Apps Script
 *
 * 설치 방법:
 * 1. https://script.google.com 접속
 * 2. 새 프로젝트 생성
 * 3. 이 코드 복사 & 붙여넣기
 * 4. 스프레드시트 ID와 솔라피 API 키 설정
 * 5. 트리거 설정 (setupTriggers 함수 실행)
 */

// ==================== 설정 ====================
const SPREADSHEET_ID = "1Y4g08k3y3CY2NDaGgFyvTC1t1QQOVXU8PE-jEYZGgKA";
const ARCHIVE_SPREADSHEET_ID = "1GE0Ge7TY_Zzgkbm2tXYpdx_NKrF15M2nq3S2FVeqWW4";  // 수업 완료 기록용
const SOLAPI_API_KEY = "NCSEFYUNADFPS4VI";
const SOLAPI_API_SECRET = "ECG86DWQEJKD2YGI3CBXDE2AOJRUBB1V";
const SENDER_NUMBER = "01012345678";  // 발신번호 (등록된 번호로 변경)
const OWNER_EMAIL = "soonjinmugu.studio@gmail.com";  // 운영자 이메일

// 시트 이름
const SHEET_RESERVATIONS = "예약목록";
const SHEET_TEMPLATES = "문자템플릿";
const SHEET_ARCHIVE = "완료";  // 완료 기록 시트

// 네이버 지도 링크
const LOCATION_LINKS = {
  "포커스": "https://naver.me/xxx",  // 실제 링크로 변경
  "시디즈": "https://naver.me/yyy",  // 실제 링크로 변경
  "강남": "https://naver.me/xxx",
  "송파/잠실": "https://naver.me/yyy"
};
// ==============================================


/**
 * 트리거 설정 (최초 1회 실행)
 */
function setupTriggers() {
  // 기존 트리거 삭제
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => ScriptApp.deleteTrigger(trigger));

  // 매일 오전 10시 트리거 (7일전 문자 + 당일 문자 + 운영자 이메일)
  ScriptApp.newTrigger('sendMorningNotifications')
    .timeBased()
    .everyDays(1)
    .atHour(10)
    .create();

  // 매일 오후 5시 30분 트리거 (종료 문자)
  ScriptApp.newTrigger('sendEveningNotifications')
    .timeBased()
    .everyDays(1)
    .atHour(17)
    .nearMinute(30)
    .create();

  Logger.log("트리거 설정 완료!");
}


/**
 * 오전 10시 알림 (7일전 + 당일 + 운영자 이메일)
 */
function sendMorningNotifications() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(SHEET_RESERVATIONS);
  const data = sheet.getDataRange().getValues();

  const today = new Date();
  const sevenDaysLater = new Date(today);
  sevenDaysLater.setDate(sevenDaysLater.getDate() + 7);

  const todayStr = formatDate(today);
  const sevenDaysStr = formatDate(sevenDaysLater);

  // 템플릿 가져오기
  const template7Days = getTemplate("7일전");
  const templateToday = getTemplate("당일");

  // 당일 수업 정보 수집 (운영자 이메일용)
  const todayClasses = [];

  // 현재 시트 컬럼 구조:
  // A: 수업일자, B: 수업시간, C: 수강생이름, D: 전화번호, E: 인원수, F: 장소명
  // G: 1주전발송, H: 당일발송, I: 종료후발송, J: 이미지링크

  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const dateStr = row[0];   // A열: 수업일자 (26년 2월 7일)
    const timeStr = row[1];   // B열: 수업시간 (14시-17시)
    const name = row[2];      // C열: 수강생이름
    const phone = row[3];     // D열: 전화번호
    const location = row[5];  // F열: 장소명
    const classTitle = "";    // 수업명 없음
    const platform = "";      // 플랫폼 없음
    const sent7Days = row[6]; // G열: 1주전발송
    const sentToday = row[7]; // H열: 당일발송

    if (!dateStr || !phone || phone === "미할당") continue;

    const reservationDate = parseDate(dateStr);
    if (!reservationDate) continue;

    const reservationDateStr = formatDate(reservationDate);

    // 7일 전 문자 발송
    if (reservationDateStr === sevenDaysStr && !sent7Days) {
      const message = fillTemplate(template7Days, {
        name: name,
        date: dateStr,
        time: timeStr,
        location: location,
        classTitle: classTitle
      });

      if (sendSMS(phone, message)) {
        sheet.getRange(i + 1, 7).setValue("O");  // G열에 발송 표시
        Logger.log(`7일전 문자 발송: ${name} - ${phone}`);
      }
    }

    // 당일 문자 발송
    if (reservationDateStr === todayStr && !sentToday) {
      const message = fillTemplate(templateToday, {
        name: name,
        date: dateStr,
        time: timeStr,
        location: location,
        classTitle: classTitle
      });

      if (sendSMS(phone, message)) {
        sheet.getRange(i + 1, 8).setValue("O");  // H열에 발송 표시
        Logger.log(`당일 문자 발송: ${name} - ${phone}`);
      }

      // 당일 수업 정보 수집
      todayClasses.push({
        time: timeStr,
        name: name,
        phone: phone,
        location: location,
        classTitle: classTitle,
        platform: platform
      });
    }
  }

  // 운영자에게 이메일 발송
  if (todayClasses.length > 0) {
    sendOwnerEmail(todayClasses);
  }
}


/**
 * 오후 5시 30분 알림 (수업 종료 문자)
 */
function sendEveningNotifications() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(SHEET_RESERVATIONS);
  const data = sheet.getDataRange().getValues();

  const today = new Date();
  const todayStr = formatDate(today);

  // 종료 템플릿 가져오기
  const templateEnd = getTemplate("종료");

  // 현재 시트 컬럼 구조:
  // A: 수업일자, B: 수업시간, C: 수강생이름, D: 전화번호, E: 인원수, F: 장소명
  // G: 1주전발송, H: 당일발송, I: 종료후발송, J: 이미지링크

  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const dateStr = row[0];   // A열: 수업일자
    const timeStr = row[1];   // B열: 수업시간
    const name = row[2];      // C열: 수강생이름
    const phone = row[3];     // D열: 전화번호
    const location = row[5];  // F열: 장소명
    const classTitle = "";    // 수업명 없음
    const sentEnd = row[8];   // I열: 종료후발송

    if (!dateStr || !phone || phone === "미할당") continue;

    const reservationDate = parseDate(dateStr);
    if (!reservationDate) continue;

    const reservationDateStr = formatDate(reservationDate);

    // 당일 종료 문자 발송
    if (reservationDateStr === todayStr && !sentEnd) {
      const message = fillTemplate(templateEnd, {
        name: name,
        date: dateStr,
        time: timeStr,
        location: location,
        classTitle: classTitle
      });

      // 종료 문자는 MMS로 발송 (사진 포함)
      const imageUrl = row[9];  // J열: 이미지링크

      let messageSent = false;

      if (imageUrl) {
        if (sendMMS(phone, message, imageUrl)) {
          sheet.getRange(i + 1, 9).setValue("O");  // I열에 발송 표시
          Logger.log(`종료 MMS 발송: ${name} - ${phone}`);
          messageSent = true;
        }
      } else {
        if (sendSMS(phone, message)) {
          sheet.getRange(i + 1, 9).setValue("O");  // I열에 발송 표시
          Logger.log(`종료 SMS 발송: ${name} - ${phone}`);
          messageSent = true;
        }
      }

      // 종료 문자 발송 성공 시 완료 기록 저장
      if (messageSent) {
        archiveCompletedClass(row);
      }
    }
  }
}


/**
 * 수업 완료 데이터를 별도 스프레드시트에 저장
 */
function archiveCompletedClass(rowData) {
  try {
    const archiveSS = SpreadsheetApp.openById(ARCHIVE_SPREADSHEET_ID);
    let archiveSheet = archiveSS.getSheetByName(SHEET_ARCHIVE);

    // 시트가 없으면 생성
    if (!archiveSheet) {
      archiveSheet = archiveSS.insertSheet(SHEET_ARCHIVE);
      // 헤더 추가
      archiveSheet.getRange(1, 1, 1, 12).setValues([[
        "일자", "수업시간", "플랫폼", "이름", "전화번호", "장소",
        "수업명", "가격", "수수료", "장소대여료", "실수령액", "기록시간"
      ]]);
      // 헤더 스타일
      archiveSheet.getRange(1, 1, 1, 12)
        .setBackground("#4A90D9")
        .setFontColor("#FFFFFF")
        .setFontWeight("bold");
    }

    // 데이터 추출 (현재 시트 구조에 맞게)
    // 원본: A:수업일자, B:수업시간, C:수강생이름, D:전화번호, E:인원수, F:장소명
    const archiveRow = [
      rowData[0] || "",   // A: 수업일자
      rowData[1] || "",   // B: 수업시간
      "",                 // 플랫폼 (없음)
      rowData[2] || "",   // C: 수강생이름
      rowData[3] || "",   // D: 전화번호
      rowData[5] || "",   // F: 장소명
      "",                 // 수업명 (없음)
      "",                 // 가격 (없음)
      "",                 // 수수료 (없음)
      "",                 // 장소대여료 (없음)
      "",                 // 실수령액 (없음)
      new Date().toLocaleString('ko-KR')  // 기록 시간
    ];

    // 마지막 행에 추가
    archiveSheet.appendRow(archiveRow);
    Logger.log(`완료 기록 저장: ${rowData[3]} - ${rowData[0]}`);

  } catch (e) {
    Logger.log(`완료 기록 저장 실패: ${e}`);
  }
}


/**
 * 운영자에게 당일 수업 정보 이메일 발송
 */
function sendOwnerEmail(classes) {
  let body = "오늘의 수업 일정입니다.\n\n";
  body += "=" .repeat(40) + "\n\n";

  classes.forEach((cls, idx) => {
    const mapLink = getLocationLink(cls.location);

    body += `[${idx + 1}] ${cls.time}\n`;
    body += `수업명: ${cls.classTitle}\n`;
    body += `수강생: ${cls.name} (${cls.phone})\n`;
    body += `장소: ${cls.location}\n`;
    body += `플랫폼: ${cls.platform}\n`;
    if (mapLink) {
      body += `지도: ${mapLink}\n`;
    }
    body += "\n" + "-".repeat(30) + "\n\n";
  });

  body += `\n총 ${classes.length}명 수업 예정`;

  const subject = `[순진무구] 오늘 수업 안내 (${classes.length}명)`;

  GmailApp.sendEmail(OWNER_EMAIL, subject, body);
  Logger.log(`운영자 이메일 발송 완료: ${classes.length}건`);
}


/**
 * 솔라피 SMS 발송
 */
function sendSMS(to, text) {
  const url = "https://api.solapi.com/messages/v4/send";

  const payload = {
    message: {
      to: to.replace(/-/g, ""),
      from: SENDER_NUMBER,
      text: text
    }
  };

  const options = {
    method: "post",
    contentType: "application/json",
    headers: getAuthHeaders(),
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  try {
    const response = UrlFetchApp.fetch(url, options);
    const result = JSON.parse(response.getContentText());

    if (response.getResponseCode() === 200) {
      return true;
    } else {
      Logger.log(`SMS 발송 실패: ${JSON.stringify(result)}`);
      return false;
    }
  } catch (e) {
    Logger.log(`SMS 발송 오류: ${e}`);
    return false;
  }
}


/**
 * 솔라피 MMS 발송 (이미지 포함)
 */
function sendMMS(to, text, imageUrl) {
  const url = "https://api.solapi.com/messages/v4/send";

  const payload = {
    message: {
      to: to.replace(/-/g, ""),
      from: SENDER_NUMBER,
      text: text,
      imageId: imageUrl  // 솔라피에 업로드된 이미지 ID
    }
  };

  const options = {
    method: "post",
    contentType: "application/json",
    headers: getAuthHeaders(),
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  try {
    const response = UrlFetchApp.fetch(url, options);
    const result = JSON.parse(response.getContentText());

    if (response.getResponseCode() === 200) {
      return true;
    } else {
      Logger.log(`MMS 발송 실패: ${JSON.stringify(result)}`);
      return false;
    }
  } catch (e) {
    Logger.log(`MMS 발송 오류: ${e}`);
    return false;
  }
}


/**
 * 솔라피 인증 헤더 생성
 */
function getAuthHeaders() {
  const date = new Date().toISOString().replace(/\.\d{3}Z$/, '.000Z');
  const salt = Utilities.getUuid();

  const signature = Utilities.computeHmacSha256Signature(
    date + salt,
    SOLAPI_API_SECRET
  );

  const signatureHex = signature.map(b => {
    return ('0' + (b & 0xFF).toString(16)).slice(-2);
  }).join('');

  return {
    'Authorization': `HMAC-SHA256 apiKey=${SOLAPI_API_KEY}, date=${date}, salt=${salt}, signature=${signatureHex}`
  };
}


/**
 * 템플릿 가져오기
 */
function getTemplate(templateName) {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(SHEET_TEMPLATES);

  if (!sheet) {
    Logger.log(`템플릿 시트를 찾을 수 없습니다: ${SHEET_TEMPLATES}`);
    return "";
  }

  const data = sheet.getDataRange().getValues();

  for (let i = 0; i < data.length; i++) {
    if (data[i][0] === templateName) {
      return data[i][1];  // B열: 템플릿 내용
    }
  }

  Logger.log(`템플릿을 찾을 수 없습니다: ${templateName}`);
  return "";
}


/**
 * 템플릿 변수 치환
 */
function fillTemplate(template, vars) {
  let result = template;

  for (const key in vars) {
    result = result.replace(new RegExp(`{${key}}`, 'g'), vars[key] || '');
  }

  return result;
}


/**
 * 날짜 문자열 파싱
 */
function parseDate(dateStr) {
  // "26년 2월 7일" 또는 "2026년 2월 7일" 또는 "2026-02-07" 형식
  const patterns = [
    /(\d{2})년\s*(\d{1,2})월\s*(\d{1,2})일/,  // 26년 2월 7일
    /(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일/,  // 2026년 2월 7일
    /(\d{4})-(\d{1,2})-(\d{1,2})/              // 2026-02-07
  ];

  for (const pattern of patterns) {
    const match = dateStr.match(pattern);
    if (match) {
      let year = parseInt(match[1]);
      // 2자리 연도면 2000 더하기
      if (year < 100) {
        year += 2000;
      }
      return new Date(year, parseInt(match[2]) - 1, parseInt(match[3]));
    }
  }

  return null;
}


/**
 * 시간 추출
 */
function extractTime(dateStr) {
  const match = dateStr.match(/(\d{1,2}):(\d{2})/);
  if (match) {
    return `${match[1]}:${match[2]}`;
  }
  return "";
}


/**
 * 날짜 포맷 (YYYY-MM-DD)
 */
function formatDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}


/**
 * 장소 링크 가져오기
 */
function getLocationLink(location) {
  for (const key in LOCATION_LINKS) {
    if (location.includes(key)) {
      return LOCATION_LINKS[key];
    }
  }
  return null;
}


/**
 * 테스트 함수 - 수동 실행용
 */
function testSendSMS() {
  const result = sendSMS("01012345678", "테스트 문자입니다.");
  Logger.log(`테스트 결과: ${result}`);
}


/**
 * 수동으로 오늘 날짜 알림 발송
 */
function manualSendToday() {
  sendMorningNotifications();
  Logger.log("수동 발송 완료");
}
