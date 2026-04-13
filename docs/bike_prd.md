제품 요구사항 정의서 (PRD): 지능형 오토바이 FMS
1. 문서 개요
프로젝트명: 지능형 오토바이 FMS (Fleet Management System)
목적: 오토바이 관제 사업 및 AI 데이터 사업을 위한 통합 데이터 생태계를 구축합니다 [cite: 관제 시스템 아키텍쳐.jpg].
타겟 플랫폼: 웹 기반 관제 대시보드 및 운전자/관리자용 모바일 앱을 개발합니다 [cite: moto_fms_architecture.html].
2. 비즈니스 목표 (제품 비전)
데이터 기반 반복 수익 창출: 단발성 수익이 아닌 데이터 기반의 반복 수익(Recurring Revenue) 구조를 마련합니다 [cite: 관제 시스템 아키텍쳐.jpg].
신규 수익 모델 연계: 수집된 데이터를 바탕으로 보험사(맞춤형 상품), 금융사(자산 가치 평가), 기업 ESG(탄소 절감 리포트) 연계 수익 모델을 구축합니다 [cite: 관제 시스템 아키텍쳐.jpg].
3. 이해관계자 및 역할
서비스 사업자 (Service Provider): 전체 시스템 및 서비스를 총괄하며, 관제 대시보드를 사용하는 주체입니다 [cite: 관제 시스템 아키텍쳐.jpg].
하도급사:
데이터 수집 노드(ION)를 관리합니다 [cite: 관제 시스템 아키텍쳐.jpg].
서버 및 앱을 운영합니다 [cite: 관제 시스템 아키텍쳐.jpg].
IoT 회선, 서비스 플랫폼, 장비 렌탈 등 안정적인 인프라 유지보수를 담당합니다 [cite: 관제 시스템 아키텍쳐.jpg].
4. 시스템 아키텍처 및 데이터 흐름
4.1. 데이터 수집 계층 (Device Layer)
ION 수집 노드: 이동형 데이터 수집 단말을 오토바이에 장착합니다 [cite: moto_fms_architecture.html].
센서 데이터:
GPS: 위치, 속도, 방향각을 수집합니다 [cite: moto_fms_architecture.html].
OBD: 엔진, RPM, 연료 상태를 진단합니다 [cite: moto_fms_architecture.html].
BMS: 배터리의 전압, 전류, 온도 등 실시간 데이터를 확보하고 상태를 파악합니다 [cite: 관제 시스템 아키텍쳐.jpg, moto_fms_architecture.html].
블랙박스: 실시간 영상 및 이벤트를 기록합니다 [cite: 관제 시스템 아키텍쳐.jpg, moto_fms_architecture.html].
4.2. 통신 및 인프라 계층 (Connectivity & Infra)
네트워크: LTE/5G 모바일 통신망을 활용합니다 [cite: moto_fms_architecture.html]. KT IoT 인프라를 활용할 수 있습니다 [cite: 관제 시스템 아키텍쳐.jpg].
프로토콜 및 서버: MQTT, HTTP 프로토콜을 통해 단말 데이터를 전송합니다 [cite: 관제 시스템 아키텍쳐.jpg]. API 게이트웨이, MQTT 브로커, TLS 암호화, WebSocket 서버, 로드 밸런서, 메시지 큐를 통해 데이터를 1차 처리하고 수신합니다 [cite: 관제 시스템 아키텍쳐.jpg, moto_fms_architecture.html].
4.3. 지능형 분석 및 데이터 처리 (Processing & AI)
AI 분석 엔진: 과속 및 급가속 등 위험 운행을 분석하고 사고를 감지합니다 [cite: 관제 시스템 아키텍쳐.jpg, moto_fms_architecture.html].
최적화 시스템: 배터리 수명을 예측하고, 최적 배차 및 이동 경로를 관리합니다 [cite: 관제 시스템 아키텍쳐.jpg, moto_fms_architecture.html].
4.4. 저장 및 시각화 계층 (Data & Client Layer)
데이터베이스: 통합 데이터 관리를 위해 시계열 DB(운행 이력 저장)와 Redis 캐시(실시간 데이터 관리)를 사용합니다 [cite: 관제 시스템 아키텍쳐.jpg, moto_fms_architecture.html].
API: GIS 및 지도 API를 연동합니다 [cite: 관제 시스템 아키텍쳐.jpg, moto_fms_architecture.html].


5. 핵심 화면 및 기능 요구사항
5.1. 관제 대시보드 (Web)
실시간 지도 모니터링: GIS API를 활용하여 맵 상에 오토바이의 실시간 위치를 핀(Pin) 형태로 추적 및 표시합니다 [cite: moto_fms_architecture.html].
차량 상태 정보 제공: 특정 차량의 현재 위치, 현재 속도, 배터리 상태, 엔진 온도를 실시간으로 표출합니다 [cite: moto_fms_architecture.html].
이벤트 알림 (Alerts): WebSocket을 활용한 실시간 Push로 위험 및 알림 사항을 표출합니다 [cite: 관제 시스템 아키텍쳐.jpg, moto_fms_architecture.html].
배터리 교체 권고 및 충전소 안내: 배터리 잔량 부족 또는 교체 주기 도래 시 알림을 발생시키며, 동시에 현재 위치에서 가장 가까운 충전소(Charging Station) 정보를 지도에 표시하고 경로를 안내합니다 [cite: moto_fms_architecture.html].
과속 감지: 차량별 위험 운행 실시간 경고 [cite: moto_fms_architecture.html].
배송 완료: 업무 완료 상태 업데이트 [cite: moto_fms_architecture.html].
5.2. 모바일 앱 (운전자 및 관리자용)
운행 목록 및 상태 조회: 개별 차량번호 및 위치와 함께 '운행중', '배송 완료', '정차(충전 중)' 등의 배지를 통해 실시간 상태를 확인합니다 [cite: moto_fms_architecture.html].
지능형 알림 및 가이드:
충전소 연동 가이드: 배터리 교체 알림 수신 시, 운전자가 즉시 가까운 충전소를 탐색하고 네비게이션으로 연동할 수 있는 숏컷 기능을 제공합니다 [cite: moto_fms_architecture.html].
통합 알림: Push 및 SMS 형태로 주요 정보 및 경고를 수신합니다 [cite: 관제 시스템 아키텍쳐.jpg].


6. 기술 스택 및 개발 환경
Frontend Framework: Vue3
Build Tool: Vite
Programming Language: TypeScript
Styling: TailwindCSS v3
Project Structure: src/components, src/views 등을 포함한 모듈화된 디렉터리 구조


7. 향후 추진 업무 (To-do List)
엔진 고도화: AI 분석 엔진 정밀도 향상 및 실시간 데이터 처리 성능 최적화 [cite: 관제 시스템 아키텍쳐.jpg].
서비스 확장: 서드파티(보험, 금융, ESG) 데이터 연동 API 확장 [cite: 관제 시스템 아키텍쳐.jpg].
인프라: 글로벌 IoT 네트워크 확장 및 보안/개인정보 보호 시스템 강화 [cite: 관제 시스템 아키텍쳐.jpg].


References
관제 시스템 아키텍쳐.jpg
moto_fms_architecture.html

