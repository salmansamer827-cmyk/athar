class Wallet {
  final int userId;
  final double vestraPoints;
  final double usdt;
  final double usdc;

  const Wallet({
    required this.userId,
    required this.vestraPoints,
    required this.usdt,
    required this.usdc,
  });

  factory Wallet.fromJson(Map<String, dynamic> json) {
    final balances =
        Map<String, dynamic>.from(json['balances'] ?? {});

    return Wallet(
      userId: json['user_id'] ?? 0,
      vestraPoints:
          (balances['vestra_points'] ?? 0).toDouble(),
      usdt: (balances['usdt'] ?? 0).toDouble(),
      usdc: (balances['usdc'] ?? 0).toDouble(),
    );
  }
}
