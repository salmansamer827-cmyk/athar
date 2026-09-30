class DashboardSummary {
  final String totalValue;
  final String principal;
  final String profit;
  final String roiPercent;
  final String usdt;
  final String usdc;
  final String points;
  final String product;
  final String status;
  final String nav;

  const DashboardSummary({
    required this.totalValue,
    required this.principal,
    required this.profit,
    required this.roiPercent,
    required this.usdt,
    required this.usdc,
    required this.points,
    required this.product,
    required this.status,
    required this.nav,
  });

  factory DashboardSummary.fromJson(Map<String, dynamic> json) {
    final p = json['portfolio'] as Map<String, dynamic>;
    final w = json['wallets'] as Map<String, dynamic>;
    final i = json['investment'] as Map<String, dynamic>;

    return DashboardSummary(
      totalValue: p['total_value'].toString(),
      principal: p['principal'].toString(),
      profit: p['profit'].toString(),
      roiPercent: p['roi_percent'].toString(),
      usdt: w['usdt'].toString(),
      usdc: w['usdc'].toString(),
      points: w['points'].toString(),
      product: i['product'].toString(),
      status: i['status'].toString(),
      nav: i['nav'].toString(),
    );
  }
}
