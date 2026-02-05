/**
 * 순진무구 수업관리 시트 디자인 및 데이터 정리
 *
 * 사용법:
 * 1. 구글 시트에서 확장 프로그램 > Apps Script
 * 2. 이 코드 붙여넣기
 * 3. formatSheet() 함수 실행
 */

/**
 * 시트 전체 포맷 적용 (메인 함수)
 */
function formatSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName("예약목록");

  if (!sheet) {
    SpreadsheetApp.getUi().alert("'예약목록' 시트를 찾을 수 없습니다.");
    return;
  }

  // 1. 헤더 설정
  setupHeaders(sheet);

  // 2. 기존 데이터 날짜/시간 분리
  fixDateTimeFormat(sheet);

  // 3. 스타일 적용
  applyStyles(sheet);

  // 4. 열 너비 조정
  adjustColumnWidths(sheet);

  // 5. 조건부 서식 추가
  addConditionalFormatting(sheet);

  SpreadsheetApp.getUi().alert("시트 포맷 완료!");
}


/**
 * 헤더 설정
 */
function setupHeaders(sheet) {
  const headers = [
    "일자",           // A
    "수업시간",       // B
    "플랫폼",         // C
    "이름",           // D
    "전화번호",       // E
    "장소",           // F
    "수업명",         // G
    "가격",           // H
    "수수료",         // I
    "장소대여료",     // J
    "실수령액",       // K
    "상태",           // L
    "7일전",          // M
    "당일",           // N
    "종료",           // O
    "종료사진URL"     // P
  ];

  // 헤더 입력
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
}


/**
 * 기존 날짜/시간 데이터 분리
 */
function fixDateTimeFormat(sheet) {
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return; // 헤더만 있으면 스킵

  const dataRange = sheet.getRange(2, 1, lastRow - 1, 2); // A2:B
  const data = dataRange.getValues();

  const updatedData = data.map(row => {
    const dateTimeStr = row[0] ? row[0].toString() : "";
    const existingTime = row[1] ? row[1].toString() : "";

    // 이미 분리된 경우 스킵
    if (existingTime && existingTime.includes("시")) {
      return row;
    }

    // 날짜/시간 분리
    const parsed = parseDateTimeString(dateTimeStr);
    return [parsed.date, parsed.time];
  });

  dataRange.setValues(updatedData);
}


/**
 * 날짜/시간 문자열 파싱
 */
function parseDateTimeString(str) {
  if (!str) return { date: "", time: "" };

  // 패턴 1: "2026년 2월 7일 14:00" 또는 "26년 2월 7일 14:00"
  let match = str.match(/(\d{2,4})년\s*(\d{1,2})월\s*(\d{1,2})일?\s*(\d{1,2}):(\d{2})/);
  if (match) {
    let year = match[1];
    if (year.length === 4) year = year.slice(-2); // 2026 -> 26
    const month = parseInt(match[2]);
    const day = parseInt(match[3]);
    const hour = parseInt(match[4]);
    const endHour = hour + 3;

    return {
      date: `${year}년 ${month}월 ${day}일`,
      time: `${hour}시-${endHour}시`
    };
  }

  // 패턴 2: "2026-02-07 14:00"
  match = str.match(/(\d{4})-(\d{1,2})-(\d{1,2})\s*(\d{1,2}):(\d{2})/);
  if (match) {
    const year = match[1].slice(-2);
    const month = parseInt(match[2]);
    const day = parseInt(match[3]);
    const hour = parseInt(match[4]);
    const endHour = hour + 3;

    return {
      date: `${year}년 ${month}월 ${day}일`,
      time: `${hour}시-${endHour}시`
    };
  }

  // 이미 "26년 2월 7일" 형식인 경우
  if (str.match(/\d{2}년\s*\d{1,2}월\s*\d{1,2}일/) && !str.includes(":")) {
    return { date: str, time: "" };
  }

  return { date: str, time: "" };
}


/**
 * 스타일 적용
 */
function applyStyles(sheet) {
  const lastRow = Math.max(sheet.getLastRow(), 1);
  const lastCol = 16; // P열까지

  // 전체 폰트 설정
  sheet.getRange(1, 1, lastRow, lastCol)
    .setFontFamily("Pretendard, Noto Sans KR, Arial")
    .setFontSize(10)
    .setVerticalAlignment("middle");

  // 헤더 스타일
  const headerRange = sheet.getRange(1, 1, 1, lastCol);
  headerRange
    .setBackground("#4A90D9")
    .setFontColor("#FFFFFF")
    .setFontWeight("bold")
    .setFontSize(11)
    .setHorizontalAlignment("center")
    .setBorder(true, true, true, true, true, true, "#2E5A8C", SpreadsheetApp.BorderStyle.SOLID);

  // 데이터 영역 스타일
  if (lastRow > 1) {
    const dataRange = sheet.getRange(2, 1, lastRow - 1, lastCol);
    dataRange
      .setBorder(true, true, true, true, true, true, "#E0E0E0", SpreadsheetApp.BorderStyle.SOLID);

    // 짝수 행 배경색
    for (let i = 2; i <= lastRow; i++) {
      if (i % 2 === 0) {
        sheet.getRange(i, 1, 1, lastCol).setBackground("#F8FAFC");
      } else {
        sheet.getRange(i, 1, 1, lastCol).setBackground("#FFFFFF");
      }
    }
  }

  // 플랫폼 열 중앙 정렬
  sheet.getRange(2, 3, lastRow - 1, 1).setHorizontalAlignment("center");

  // 금액 열 우측 정렬 및 숫자 포맷
  const moneyColumns = [8, 9, 10, 11]; // H, I, J, K
  moneyColumns.forEach(col => {
    if (lastRow > 1) {
      sheet.getRange(2, col, lastRow - 1, 1)
        .setHorizontalAlignment("right")
        .setNumberFormat("#,##0");
    }
  });

  // 문자 발송 여부 열 중앙 정렬
  const checkColumns = [13, 14, 15]; // M, N, O
  checkColumns.forEach(col => {
    if (lastRow > 1) {
      sheet.getRange(2, col, lastRow - 1, 1).setHorizontalAlignment("center");
    }
  });

  // 헤더 행 고정
  sheet.setFrozenRows(1);
}


/**
 * 열 너비 조정
 */
function adjustColumnWidths(sheet) {
  const widths = {
    1: 100,   // A: 일자
    2: 80,    // B: 수업시간
    3: 70,    // C: 플랫폼
    4: 70,    // D: 이름
    5: 110,   // E: 전화번호
    6: 80,    // F: 장소
    7: 200,   // G: 수업명
    8: 80,    // H: 가격
    9: 80,    // I: 수수료
    10: 80,   // J: 장소대여료
    11: 90,   // K: 실수령액
    12: 70,   // L: 상태
    13: 50,   // M: 7일전
    14: 50,   // N: 당일
    15: 50,   // O: 종료
    16: 150   // P: 종료사진URL
  };

  Object.entries(widths).forEach(([col, width]) => {
    sheet.setColumnWidth(parseInt(col), width);
  });
}


/**
 * 조건부 서식 추가
 */
function addConditionalFormatting(sheet) {
  const lastRow = sheet.getMaxRows();

  // 기존 조건부 서식 제거
  sheet.clearConditionalFormatRules();

  const rules = [];

  // 플랫폼별 색상 (C열)
  // 프립: 파란색 배경
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenTextEqualTo("프립")
    .setBackground("#E3F2FD")
    .setRanges([sheet.getRange(2, 3, lastRow - 1, 1)])
    .build());

  // 솜씨당: 주황색 배경
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenTextEqualTo("솜씨당")
    .setBackground("#FFF3E0")
    .setRanges([sheet.getRange(2, 3, lastRow - 1, 1)])
    .build());

  // 문자 발송 완료 (O 표시): 녹색 배경
  const checkColumns = ["M", "N", "O"];
  checkColumns.forEach((col, idx) => {
    rules.push(SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("O")
      .setBackground("#E8F5E9")
      .setFontColor("#2E7D32")
      .setRanges([sheet.getRange(`${col}2:${col}${lastRow}`)])
      .build());
  });

  // 실수령액 하이라이트 (K열) - 6만원 이상 녹색
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThanOrEqualTo(60000)
    .setBackground("#C8E6C9")
    .setRanges([sheet.getRange(2, 11, lastRow - 1, 1)])
    .build());

  sheet.setConditionalFormatRules(rules);
}


/**
 * 템플릿 시트 생성/포맷
 */
function formatTemplateSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName("템플릿");

  if (!sheet) {
    sheet = ss.insertSheet("템플릿");
  }

  // 헤더
  sheet.getRange(1, 1, 1, 2).setValues([["템플릿명", "내용"]]);
  sheet.getRange(1, 1, 1, 2)
    .setBackground("#4A90D9")
    .setFontColor("#FFFFFF")
    .setFontWeight("bold");

  // 기본 템플릿 추가 (빈 경우)
  if (sheet.getLastRow() <= 1) {
    const templates = [
      ["7일전", "안녕하세요 {name}님! 순진무구입니다.\n\n{date} {time} 수업이 7일 앞으로 다가왔습니다.\n\n장소: {location}\n수업명: {classTitle}\n\n궁금하신 점 있으시면 편하게 연락주세요!"],
      ["당일", "안녕하세요 {name}님!\n\n오늘 {time} 수업이 있습니다.\n\n장소: {location}\n\n수업에서 뵙겠습니다! 😊"],
      ["종료", "{name}님, 오늘 수업 수고하셨습니다!\n\n즐거운 시간이 되셨길 바랍니다.\n다음에 또 만나요! 🎨"]
    ];
    sheet.getRange(2, 1, templates.length, 2).setValues(templates);
  }

  // 열 너비
  sheet.setColumnWidth(1, 100);
  sheet.setColumnWidth(2, 500);

  // 내용 열 줄바꿈
  sheet.getRange(2, 2, sheet.getLastRow() - 1, 1).setWrap(true);

  SpreadsheetApp.getUi().alert("템플릿 시트 설정 완료!");
}


/**
 * 메뉴 추가
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🎨 순진무구')
    .addItem('예약목록 시트 포맷 적용', 'formatSheet')
    .addItem('🌟 CRM 스타일 적용', 'applyCRMStyleDesign')
    .addItem('템플릿 시트 설정', 'formatTemplateSheet')
    .addItem('완료 기록 시트 포맷', 'formatArchiveSheet')
    .addSeparator()
    .addItem('날짜/시간 형식 수정', 'fixDateTimeFormat_manual')
    .addToUi();
}


/**
 * CRM 스타일 디자인 적용 (노란 헤더 + 검정 섹션 헤더)
 * 이미지 참조 디자인과 유사하게 적용
 */
function applyCRMStyleDesign() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName("예약목록");

  if (!sheet) {
    SpreadsheetApp.getUi().alert("'예약목록' 시트를 찾을 수 없습니다.");
    return;
  }

  const lastRow = Math.max(sheet.getLastRow(), 20);
  const lastCol = 16; // P열까지

  // ========================================
  // 1. 전체 배경 흰색으로 초기화
  // ========================================
  sheet.getRange(1, 1, lastRow + 5, lastCol + 2)
    .setBackground("#FFFFFF")
    .clearFormat();

  // ========================================
  // 2. 타이틀 영역 (1행) - 노란색 배경
  // ========================================
  sheet.insertRowBefore(1);
  sheet.insertRowBefore(1);

  // 타이틀 행 (노란색)
  const titleRange = sheet.getRange(1, 1, 1, lastCol);
  titleRange.merge();
  titleRange.setValue("📋 순진무구 수업관리");
  titleRange
    .setBackground("#FFC107")  // 노란색
    .setFontColor("#000000")
    .setFontSize(16)
    .setFontWeight("bold")
    .setHorizontalAlignment("center")
    .setVerticalAlignment("middle");
  sheet.setRowHeight(1, 45);

  // 부제목/상태 행
  const subtitleRange = sheet.getRange(2, 1, 1, lastCol);
  subtitleRange.merge();
  subtitleRange.setValue("프립 & 솜씨당 예약 통합 관리 시스템");
  subtitleRange
    .setBackground("#FFF8E1")  // 연한 노란색
    .setFontColor("#5D4037")
    .setFontSize(11)
    .setFontStyle("italic")
    .setHorizontalAlignment("center");
  sheet.setRowHeight(2, 30);

  // ========================================
  // 3. 섹션 헤더 (3행) - 검정 배경 + 흰 글씨
  // ========================================
  const sectionHeaderRange = sheet.getRange(3, 1, 1, lastCol);
  sectionHeaderRange.merge();
  sectionHeaderRange.setValue("1. 예약 목록");
  sectionHeaderRange
    .setBackground("#212121")  // 검정
    .setFontColor("#FFFFFF")   // 흰색
    .setFontSize(12)
    .setFontWeight("bold")
    .setHorizontalAlignment("left")
    .setVerticalAlignment("middle");
  sheet.setRowHeight(3, 35);

  // ========================================
  // 4. 컬럼 헤더 (4행)
  // ========================================
  const headers = [
    "일자", "수업시간", "플랫폼", "이름", "전화번호", "장소",
    "수업명", "가격", "수수료", "장소대여료", "실수령액", "상태",
    "7일전", "당일", "종료", "사진URL"
  ];

  const headerRange = sheet.getRange(4, 1, 1, headers.length);
  headerRange.setValues([headers]);
  headerRange
    .setBackground("#424242")  // 진한 회색
    .setFontColor("#FFFFFF")
    .setFontWeight("bold")
    .setFontSize(10)
    .setHorizontalAlignment("center")
    .setVerticalAlignment("middle")
    .setBorder(true, true, true, true, true, true, "#212121", SpreadsheetApp.BorderStyle.SOLID);
  sheet.setRowHeight(4, 32);

  // ========================================
  // 5. 데이터 영역 스타일
  // ========================================
  const dataStartRow = 5;
  const dataRows = lastRow - 2; // 추가된 행 고려

  if (dataRows > 0) {
    const dataRange = sheet.getRange(dataStartRow, 1, dataRows, lastCol);

    // 전체 폰트 설정
    dataRange
      .setFontFamily("Pretendard, Noto Sans KR, Arial")
      .setFontSize(10)
      .setVerticalAlignment("middle")
      .setBorder(true, true, true, true, true, true, "#E0E0E0", SpreadsheetApp.BorderStyle.SOLID);

    // 줄무늬 배경
    for (let i = dataStartRow; i < dataStartRow + dataRows; i++) {
      const rowRange = sheet.getRange(i, 1, 1, lastCol);
      if ((i - dataStartRow) % 2 === 0) {
        rowRange.setBackground("#FFFFFF");
      } else {
        rowRange.setBackground("#FAFAFA");
      }
    }

    // 금액 열 포맷
    [8, 9, 10, 11].forEach(col => {
      sheet.getRange(dataStartRow, col, dataRows, 1)
        .setHorizontalAlignment("right")
        .setNumberFormat("#,##0");
    });

    // 중앙 정렬 열
    [3, 12, 13, 14, 15].forEach(col => {
      sheet.getRange(dataStartRow, col, dataRows, 1)
        .setHorizontalAlignment("center");
    });
  }

  // ========================================
  // 6. 열 너비 조정
  // ========================================
  const widths = {
    1: 95,   // 일자
    2: 80,   // 수업시간
    3: 65,   // 플랫폼
    4: 65,   // 이름
    5: 105,  // 전화번호
    6: 75,   // 장소
    7: 180,  // 수업명
    8: 75,   // 가격
    9: 70,   // 수수료
    10: 75,  // 장소대여료
    11: 85,  // 실수령액
    12: 60,  // 상태
    13: 50,  // 7일전
    14: 50,  // 당일
    15: 50,  // 종료
    16: 120  // 사진URL
  };

  Object.entries(widths).forEach(([col, width]) => {
    sheet.setColumnWidth(parseInt(col), width);
  });

  // ========================================
  // 7. 조건부 서식
  // ========================================
  sheet.clearConditionalFormatRules();
  const rules = [];

  // 플랫폼별 색상
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenTextEqualTo("프립")
    .setBackground("#E3F2FD")
    .setFontColor("#1565C0")
    .setRanges([sheet.getRange(dataStartRow, 3, sheet.getMaxRows() - dataStartRow + 1, 1)])
    .build());

  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenTextEqualTo("솜씨당")
    .setBackground("#FFF3E0")
    .setFontColor("#E65100")
    .setRanges([sheet.getRange(dataStartRow, 3, sheet.getMaxRows() - dataStartRow + 1, 1)])
    .build());

  // 문자 발송 완료 표시
  ["M", "N", "O"].forEach(col => {
    rules.push(SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("O")
      .setBackground("#C8E6C9")
      .setFontColor("#2E7D32")
      .setRanges([sheet.getRange(`${col}${dataStartRow}:${col}`)])
      .build());
  });

  sheet.setConditionalFormatRules(rules);

  // ========================================
  // 8. 헤더 고정
  // ========================================
  sheet.setFrozenRows(4);

  SpreadsheetApp.getUi().alert("✅ CRM 스타일 디자인 적용 완료!");
}


/**
 * 날짜/시간 형식 수동 수정
 */
function fixDateTimeFormat_manual() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName("예약목록");

  if (!sheet) {
    SpreadsheetApp.getUi().alert("'예약목록' 시트를 찾을 수 없습니다.");
    return;
  }

  fixDateTimeFormat(sheet);
  SpreadsheetApp.getUi().alert("날짜/시간 형식 수정 완료!");
}


/**
 * 완료 기록 시트 포맷 (별도 스프레드시트)
 * 수업 완료 기록 시트 ID: 1GE0Ge7TY_Zzgkbm2tXYpdx_NKrF15M2nq3S2FVeqWW4
 */
function formatArchiveSheet() {
  const ARCHIVE_ID = "1GE0Ge7TY_Zzgkbm2tXYpdx_NKrF15M2nq3S2FVeqWW4";

  try {
    const ss = SpreadsheetApp.openById(ARCHIVE_ID);
    let sheet = ss.getSheetByName("완료");

    if (!sheet) {
      sheet = ss.insertSheet("완료");
    }

    // 헤더 설정
    const headers = [
      "일자", "수업시간", "플랫폼", "이름", "전화번호", "장소",
      "수업명", "가격", "수수료", "장소대여료", "실수령액", "기록시간"
    ];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);

    const lastRow = Math.max(sheet.getLastRow(), 1);

    // 헤더 스타일
    sheet.getRange(1, 1, 1, headers.length)
      .setBackground("#2E7D32")  // 녹색 (완료 표시)
      .setFontColor("#FFFFFF")
      .setFontWeight("bold")
      .setFontSize(11)
      .setHorizontalAlignment("center");

    // 데이터 영역 스타일
    if (lastRow > 1) {
      // 짝수 행 배경색
      for (let i = 2; i <= lastRow; i++) {
        if (i % 2 === 0) {
          sheet.getRange(i, 1, 1, headers.length).setBackground("#F1F8E9");
        } else {
          sheet.getRange(i, 1, 1, headers.length).setBackground("#FFFFFF");
        }
      }

      // 금액 열 숫자 포맷
      [8, 9, 10, 11].forEach(col => {
        sheet.getRange(2, col, lastRow - 1, 1)
          .setHorizontalAlignment("right")
          .setNumberFormat("#,##0");
      });
    }

    // 열 너비 조정
    const widths = {
      1: 100, 2: 80, 3: 70, 4: 70, 5: 110, 6: 80,
      7: 200, 8: 80, 9: 80, 10: 80, 11: 90, 12: 140
    };
    Object.entries(widths).forEach(([col, width]) => {
      sheet.setColumnWidth(parseInt(col), width);
    });

    // 헤더 고정
    sheet.setFrozenRows(1);

    // 플랫폼별 조건부 서식
    const rules = [];
    rules.push(SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("프립")
      .setBackground("#E3F2FD")
      .setRanges([sheet.getRange(2, 3, sheet.getMaxRows() - 1, 1)])
      .build());
    rules.push(SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("솜씨당")
      .setBackground("#FFF3E0")
      .setRanges([sheet.getRange(2, 3, sheet.getMaxRows() - 1, 1)])
      .build());
    sheet.setConditionalFormatRules(rules);

    SpreadsheetApp.getUi().alert("완료 기록 시트 포맷 완료!");

  } catch (e) {
    SpreadsheetApp.getUi().alert("오류: " + e.message);
  }
}
