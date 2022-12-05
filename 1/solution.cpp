#ifndef __PROGTEST__
#include <cassert>
#include <cfloat>
#include <climits>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>

#include "progtest_solver.h"
#include "sample_tester.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <deque>
#include <functional>
#include <iomanip>
#include <iostream>
#include <list>
#include <map>
#include <memory>
#include <mutex>
#include <numeric>
#include <queue>
#include <set>
#include <stack>
#include <thread>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#endif /* __PROGTEST__ */

class CSentinelHacker {
public:
  CSentinelHacker();
  static bool SeqSolve(const std::vector<uint64_t> &fragments, CBigInt &res);
  void AddTransmitter(ATransmitter x);
  void AddReceiver(AReceiver x);
  void AddFragment(uint64_t x);
  void Start(unsigned thrCount);
  void Stop();

private:
  void ReceiveWorker(const AReceiver &receiver);
  void SendWorker(const ATransmitter &transmitter);
  void ComputeWorker();

  std::vector<AReceiver> receivers;
  std::vector<ATransmitter> transmitters;

  // vectors with threads (to join them later)
  std::vector<std::thread> receiveWorkerThreads;
  std::vector<std::thread> sendWorkerThreads;
  std::vector<std::thread> computeWorkerThreads;

  // map with received fragments (storing purpose) and mutex
  std::mutex fragmentsMtx;
  std::map<uint32_t, std::vector<uint64_t>> fragments;

  // a queue with new things for compute threads (+ mutex and CV)
  std::mutex toComputeMtx;
  std::condition_variable toComputeCV;
  std::queue<std::pair<uint32_t, std::vector<uint64_t>>> toCompute;

  // flags between stages
  std::atomic<bool> receiving;
  std::atomic<bool> computedAll;

  // computed problems (maximum dumped to queue to send) and mutex with
  // condition_variable
  std::mutex toSendMtx;
  std::condition_variable toSendCV;
  std::queue<std::pair<uint32_t, CBigInt>> toSend;

  std::mutex sentMtx;
  std::set<uint32_t> sent;
};

CSentinelHacker::CSentinelHacker() {
  // receive & send
  receivers.reserve(10);
  transmitters.reserve(10);

  // threads
  receiveWorkerThreads.reserve(10);
  sendWorkerThreads.reserve(10);
  computeWorkerThreads.reserve(10);
}

bool CSentinelHacker::SeqSolve(const std::vector<uint64_t> &fragments,
                               CBigInt &res) {

  std::vector<CBigInt> resolved;

  FindPermutations(fragments.data(), fragments.size(),
                   [&](const uint8_t *problem, size_t size) {
                     resolved.push_back(CountExpressions(
                         problem + 4, size - SHIFT_PAYLOAD_LEN));
                   });

  if (resolved.size() == 0) {
    return false;
  }

  res = *std::max_element(resolved.cbegin(), resolved.cend(),
                          [](const CBigInt &lhs, const CBigInt &rhs) {
                            return lhs.CompareTo(rhs) == -1;
                          });

  return true;
}

void CSentinelHacker::AddTransmitter(ATransmitter x) {
  transmitters.push_back(x);
}

void CSentinelHacker::AddReceiver(AReceiver x) { receivers.push_back(x); }

void CSentinelHacker::AddFragment(uint64_t x) {

  uint32_t id = x >> SHIFT_MSG_ID;

  std::vector<uint64_t> tmp;

  {
    std::lock_guard<std::mutex> lg(fragmentsMtx);
    fragments[id].push_back(x);
    tmp = fragments[id];
  }

  auto pair = std::pair<uint32_t, std::vector<uint64_t>>(id, tmp);

  {
    std::lock_guard<std::mutex> lg(toComputeMtx);
    toCompute.push(pair);
    toComputeCV.notify_all();
  }
}

void CSentinelHacker::ReceiveWorker(const AReceiver &receiver) {

  uint64_t fragment = 0;

  while (receiver->Recv(fragment)) {
    AddFragment(fragment);
  }
}

void CSentinelHacker::ComputeWorker() {
  using namespace std::chrono_literals;

  CBigInt result = 0;

  while (true) {

    std::unique_lock<std::mutex> lock(toComputeMtx);
    toComputeCV.wait_for(lock, 250ms, [&] { return !toCompute.empty(); });

    // locked --------------------------------------
    if (receiving.load() == false && toCompute.empty()) {
      lock.unlock();
      break;
    }

    if (toCompute.empty()) {
      lock.unlock();
      continue;
    }

    auto pair = toCompute.front();
    toCompute.pop();
    lock.unlock();
    // ---------------------------------------------

    if (SeqSolve(pair.second, result)) {
      std::pair<uint32_t, CBigInt> p(pair.first, result);

      std::lock_guard<std::mutex> lock_guard(toSendMtx);
      toSend.push(p);
      toSendCV.notify_all();
    }
  }
}

void CSentinelHacker::SendWorker(const ATransmitter &transmitter) {

  using namespace std::chrono_literals;

  while (true) {

    std::unique_lock<std::mutex> lock(toSendMtx);
    toSendCV.wait_for(lock, 250ms, [&] { return !toSend.empty(); });

    // locked --------------------------------------
    if (computedAll.load() == true && toSend.empty()) {
      lock.unlock();
      break;
    }

    if (toSend.empty()) {
      lock.unlock();
      continue;
    }

    auto result = toSend.front();
    toSend.pop();
    lock.unlock();
    // ---------------------------------------------

    // id and result
    transmitter->Send(result.first, result.second);

    std::lock_guard<std::mutex> lg(sentMtx);
    // save all sent ids, so if some new fragment will be received after
    // resolving problem and will appear in fragments map again at the end of
    // this worker it won't be sent as incomplete
    sent.insert(result.first);
  }

  std::lock_guard<std::mutex> lg(fragmentsMtx);
  for (const auto &item : fragments) {

    std::lock_guard<std::mutex> lg1(sentMtx);
    if (sent.find(item.first) == sent.end()) {
      transmitter->Incomplete(item.first);
    }
  }
}

void CSentinelHacker::Start(unsigned thrCount) {

  receiving = true;
  computedAll = false;

  // init receiver workers
  for (size_t i = 0; i < receivers.size(); i++) {
    receiveWorkerThreads.emplace_back(&CSentinelHacker::ReceiveWorker, this,
                                      std::ref(receivers[i]));
  }
  // init computing workers
  for (size_t i = 0; i < thrCount; i++) {
    computeWorkerThreads.emplace_back(&CSentinelHacker::ComputeWorker, this);
  }

  // init sender workers
  for (size_t i = 0; i < transmitters.size(); i++) {
    sendWorkerThreads.emplace_back(&CSentinelHacker::SendWorker, this,
                                   std::ref(transmitters[i]));
  }
}

void CSentinelHacker::Stop() {

  for (std::thread &t : receiveWorkerThreads) {
    if (t.joinable()) {
      t.join();
    }
  }
  receiving = false;

  for (std::thread &t : computeWorkerThreads) {
    if (t.joinable()) {
      t.join();
    }
  }

  computedAll = true;

  for (std::thread &t : sendWorkerThreads) {
    if (t.joinable()) {
      t.join();
    }
  }
}
//-------------------------------------------------------------------------------------------------
#ifndef __PROGTEST__

int main() {

  for (const auto &x : g_TestSets) {
    CBigInt res;
    assert(CSentinelHacker::SeqSolve(x.m_Fragments, res));
    assert(CBigInt(x.m_Result).CompareTo(res) == 0);
  }

  using namespace std::placeholders;

  CSentinelHacker test;
  auto trans = std::make_shared<CExampleTransmitter>();
  AReceiver recv =
      std::make_shared<CExampleReceiver>(std::initializer_list<uint64_t>{
          0x02230000000c, 0x071e124dabef, 0x02360037680e, 0x071d2f8fe0a1,
          0x055500150755});

  test.AddTransmitter(trans);
  test.AddReceiver(recv);

  test.Start(3);

  static std::initializer_list<uint64_t> t1Data = {
      0x071f6b8342ab, 0x0738011f538d, 0x0732000129c3, 0x055e6ecfa0f9,
      0x02ffaa027451, 0x02280000010b, 0x02fb0b88bc3e};
  std::thread t1(FragmentSender, bind(&CSentinelHacker::AddFragment, &test, _1),
                 t1Data);

  static std::initializer_list<uint64_t> t2Data = {
      0x073700609bbd, 0x055901d61e7b, 0x022a0000032b, 0x016f0000edfb};
  std::thread t2(FragmentSender, bind(&CSentinelHacker::AddFragment, &test, _1),
                 t2Data);
  FragmentSender(bind(&CSentinelHacker::AddFragment, &test, _1),
                 std::initializer_list<uint64_t>{0x017f4cb42a68, 0x02260000000d,
                                                 0x072500000025});

  t1.join();
  t2.join();
  test.Stop();
  assert(trans->TotalSent() == 4);
  assert(trans->TotalIncomplete() == 2);

  return 0;
}
#endif /* __PROGTEST__ */
